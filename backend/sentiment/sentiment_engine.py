import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import openai
from config import settings
import logging

logger = logging.getLogger(__name__)


class SentimentEngine:
    def __init__(self):
        self.finbert_tokenizer = None
        self.finbert_model = None
        self.openai_client = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._initialized = False
        
    async def initialize(self):
        """Initialize the sentiment analysis models"""
        if self._initialized:
            return
            
        try:
            # Initialize FinBERT
            logger.info("Loading FinBERT model...")
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL_NAME)
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(settings.FINBERT_MODEL_NAME)
            self.finbert_model.to(self.device)
            self.finbert_model.eval()
            
            # Initialize OpenAI client
            if settings.OPENAI_API_KEY:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            self._initialized = True
            logger.info("Sentiment engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize sentiment engine: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for sentiment analysis"""
        # Basic preprocessing
        text = text.strip()
        if len(text) > 512:  # FinBERT max length
            text = text[:512]
        return text
    
    async def analyze_finbert(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using FinBERT with improved scoring"""
        if not self._initialized:
            await self.initialize()
            
        # Ensure models are loaded
        if self.finbert_tokenizer is None or self.finbert_model is None:
            await self.initialize()
            
        # Type assertion for linter
        assert self.finbert_tokenizer is not None
        assert self.finbert_model is not None
            
        start_time = time.time()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Tokenize
            inputs = self.finbert_tokenizer(
                processed_text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Get predictions with probabilities
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1)
                predictions = torch.argmax(outputs.logits, dim=1)
            
            # Extract actual probability values
            probs = probabilities.cpu().numpy()[0]
            negative_prob = float(probs[0])
            neutral_prob = float(probs[1]) 
            positive_prob = float(probs[2])
            
            # Calculate more nuanced sentiment score
            # Instead of just -0.5, 0, +0.5, use actual probability-weighted score
            sentiment_score = (positive_prob - negative_prob)  # Range: -1 to +1
            
            # More granular labeling
            if sentiment_score > 0.3:
                sentiment_label = "strongly_positive"
            elif sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score > -0.1:
                sentiment_label = "neutral"
            elif sentiment_score > -0.3:
                sentiment_label = "negative"
            else:
                sentiment_label = "strongly_negative"
            
            # Confidence is the maximum probability
            confidence_score = float(probabilities.max().item())
            
            # Get embedding for vector storage
            embedding = self.finbert_model(**inputs, output_hidden_states=True).hidden_states[-1][:, 0, :].cpu().detach().numpy()
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "confidence_score": confidence_score,
                "embedding_vector": embedding.flatten().tolist(),
                "processing_time_ms": int(processing_time),
                "model_name": "finbert",
                "probability_breakdown": {
                    "negative": negative_prob,
                    "neutral": neutral_prob, 
                    "positive": positive_prob
                },
                "sentiment_strength": abs(sentiment_score),  # How strong the sentiment is
                "certainty": confidence_score  # How certain the model is
            }
            
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "confidence_score": 0.0,
                "embedding_vector": None,
                "processing_time_ms": 0,
                "model_name": "finbert",
                "error": str(e)
            }
    
    async def analyze_openai(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment using OpenAI"""
        if not self.openai_client:
            logger.warning("OpenAI client not initialized")
            return None
            
        start_time = time.time()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Create prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment of the following financial news text. 
            Provide a sentiment score between -1 (very negative) and 1 (very positive), 
            a sentiment label (positive, negative, neutral), and a confidence score.
            
            Text: {processed_text}
            
            Respond in JSON format:
            {{
                "sentiment_score": float,
                "sentiment_label": "positive|negative|neutral",
                "confidence_score": float,
                "reasoning": "brief explanation"
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse response
            content = response.choices[0].message.content
            if content is None:
                return None
                
            import json
            result = json.loads(content)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "sentiment_score": result["sentiment_score"],
                "sentiment_label": result["sentiment_label"],
                "confidence_score": result["confidence_score"],
                "reasoning": result.get("reasoning", ""),
                "processing_time_ms": int(processing_time),
                "model_name": "openai"
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    async def analyze_ensemble(self, text: str) -> Dict[str, Any]:
        """Combine FinBERT and OpenAI results for ensemble analysis with improved scoring"""
        if not self._initialized:
            await self.initialize()
        
        # Get individual analyses
        finbert_result = await self.analyze_finbert(text)
        openai_result = await self.analyze_openai(text)
        
        # If OpenAI failed, return enhanced FinBERT result
        if not openai_result:
            return finbert_result
        
        # Combine results with weighted average (favor FinBERT for financial text)
        finbert_weight = 0.7
        openai_weight = 0.3
        
        combined_score = (
            finbert_result["sentiment_score"] * finbert_weight +
            openai_result["sentiment_score"] * openai_weight
        )
        
        # Determine combined label with more granular categories
        if combined_score > 0.4:
            combined_label = "strongly_positive"
        elif combined_score > 0.15:
            combined_label = "positive"
        elif combined_score > -0.15:
            combined_label = "neutral"
        elif combined_score > -0.4:
            combined_label = "negative"
        else:
            combined_label = "strongly_negative"
        
        # Average confidence scores
        combined_confidence = (
            finbert_result["confidence_score"] * finbert_weight +
            openai_result["confidence_score"] * openai_weight
        )
        
        # Calculate sentiment strength and agreement
        sentiment_strength = abs(combined_score)
        model_agreement = 1.0 - abs(finbert_result["sentiment_score"] - openai_result["sentiment_score"]) / 2.0
        
        return {
            "sentiment_score": combined_score,
            "sentiment_label": combined_label,
            "confidence_score": combined_confidence,
            "sentiment_strength": sentiment_strength,  # How strong the sentiment is (0-1)
            "model_agreement": model_agreement,  # How much models agree (0-1)
            "certainty": combined_confidence,
            "finbert_result": finbert_result,
            "openai_result": openai_result,
            "model_name": "ensemble",
            "interpretation": self._interpret_sentiment(combined_score, sentiment_strength, model_agreement)
        }
    
    def _interpret_sentiment(self, score: float, strength: float, agreement: float) -> str:
        """Generate human-readable interpretation of sentiment analysis"""
        
        # Determine sentiment direction
        if score > 0.15:
            direction = "positive" if score < 0.4 else "very positive"
        elif score < -0.15:
            direction = "negative" if score > -0.4 else "very negative"
        else:
            direction = "neutral"
        
        # Determine confidence level
        if strength > 0.6 and agreement > 0.8:
            confidence_desc = "high confidence"
        elif strength > 0.3 and agreement > 0.6:
            confidence_desc = "moderate confidence"
        else:
            confidence_desc = "low confidence"
        
        return f"{direction.title()} sentiment with {confidence_desc}"
    
    async def analyze_batch(self, texts: List[str], model: str = "ensemble") -> List[Dict[str, Any]]:
        """Analyze multiple texts in batch"""
        if not self._initialized:
            await self.initialize()
        
        results = []
        
        # Process in batches to avoid memory issues
        batch_size = settings.SENTIMENT_BATCH_SIZE
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_tasks = []
            
            for text in batch:
                if model == "finbert":
                    task = self.analyze_finbert(text)
                elif model == "openai":
                    task = self.analyze_openai(text)
                else:
                    task = self.analyze_ensemble(text)
                batch_tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis failed for text {i + j}: {result}")
                    results.append({
                        "sentiment_score": 0.0,
                        "sentiment_label": "neutral",
                        "confidence_score": 0.0,
                        "error": str(result),
                        "model_name": model
                    })
                else:
                    results.append(result)
        
        return results


# Global sentiment engine instance
sentiment_engine = SentimentEngine()
