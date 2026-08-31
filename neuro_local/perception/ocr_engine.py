"""
OCR движок для извлечения текста
"""
from PIL import Image
from typing import List, Dict, Any
import numpy as np


class OCREngine:
    """OCR с поддержкой RapidOCR или pytesseract"""
    
    def __init__(self):
        self.rapid_ocr = None
        self.pytesseract = None
        
        # Пробуем RapidOCR
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.rapid_ocr = RapidOCR()
            print("[OCR] RapidOCR доступен")
        except ImportError:
            pass
        
        # Пробуем pytesseract
        if not self.rapid_ocr:
            try:
                import pytesseract
                self.pytesseract = pytesseract
                print("[OCR] Pytesseract доступен")
            except ImportError:
                print("[OCR] Нет доступных OCR движков - текст не будет распознан")
                
    def extract_text(self, image: Image.Image) -> str:
        """Извлекает текст с изображения"""
        if self.rapid_ocr:
            return self._extract_with_rapid(image)
        elif self.pytesseract:
            return self._extract_with_tesseract(image)
        else:
            return ""
            
    def _extract_with_rapid(self, image: Image.Image) -> str:
        """OCR через RapidOCR"""
        try:
            img_array = np.array(image)
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]  # RGBA → RGB
            
            # RapidOCR ожидает BGR
            import cv2
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            result, _ = self.rapid_ocr(img_bgr)
            if result:
                texts = [item[1] for item in result if item[1]]
                return " ".join(texts)
        except Exception as e:
            print(f"[RapidOCR] Ошибка: {e}")
        
        return ""
        
    def _extract_with_tesseract(self, image: Image.Image) -> str:
        """OCR через pytesseract"""
        try:
            text = self.pytesseract.image_to_string(image, lang='eng+rus')
            return text.strip()
        except Exception as e:
            print(f"[Tesseract] Ошибка: {e}")
            return ""
            
    def extract_text_with_coordinates(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Текст с координатами"""
        results = []
        
        if self.rapid_ocr:
            try:
                img_array = np.array(image)
                import cv2
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                ocr_result, _ = self.rapid_ocr(img_bgr)
                if ocr_result:
                    for item in ocr_result:
                        box = item[0]  # [[x1,y1], [x2,y2], ...]
                        text = item[1]
                        conf = item[2]
                        
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        
                        results.append({
                            "text": text,
                            "confidence": conf,
                            "center": {
                                "x": int(sum(xs) / len(xs)),
                                "y": int(sum(ys) / len(ys))
                            }
                        })
            except Exception as e:
                print(f"[RapidOCR coords] Ошибка: {e}")
                
        elif self.pytesseract:
            try:
                data = self.pytesseract.image_to_data(
                    image, 
                    output_type=self.pytesseract.Output.DICT,
                    lang='eng+rus'
                )
                
                n_boxes = len(data['level'])
                for i in range(n_boxes):
                    if int(data['conf'][i]) > 0 and data['text'][i].strip():
                        results.append({
                            "text": data['text'][i].strip(),
                            "confidence": int(data['conf'][i]),
                            "center": {
                                "x": int(data['left'][i] + data['width'][i]/2),
                                "y": int(data['top'][i] + data['height'][i]/2)
                            }
                        })
            except Exception as e:
                print(f"[Tesseract coords] Ошибка: {e}")
        
        return results
