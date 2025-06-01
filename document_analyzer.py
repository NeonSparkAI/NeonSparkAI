import cv2
import numpy as np
from PIL import Image
import pytesseract
import google.generativeai as genai
from pdf2image import convert_from_bytes
import io

class DocumentAnalyzer:
    def __init__(self, api_key):
        self.genai = genai
        self.genai.configure(api_key=api_key)
        self.model = self.genai.GenerativeModel('gemini-1.5-pro-latest')
        
    def preprocess_image(self, image):
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    
    def extract_text_from_image(self, image_bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess image
        processed_img = self.preprocess_image(img)
        
        # Extract text using OCR
        text = pytesseract.image_to_string(processed_img)
        
        return text
    
    def extract_text_from_pdf(self, pdf_bytes):
        # Convert PDF to images
        images = convert_from_bytes(pdf_bytes)
        
        # Extract text from each page
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
            text += "\n--- Page Break ---\n"
            
        return text
    
    async def analyze_content(self, text):
        # Generate analysis using Gemini
        prompt = """
        Analyze the following document content and provide:
        1. A detailed summary
        2. Key points and insights
        3. Any relevant recommendations
        4. Document type and purpose identification
        
        Content:
        {text}
        """
        
        response = await self.model.generate_content_async(
            prompt.format(text=text),
            generation_config={
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 2048,
            }
        )
        
        return response.text