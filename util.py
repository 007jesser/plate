import string
import easyocr
import re

# Initialize the OCR reader
reader = easyocr.Reader(['ar'], gpu=False)

dict_int_to_char = {'1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', '0': '0'}
dict_char_to_int = {'ت': 'T', 'و': 'U', 'ن': 'N', 'س': 'S'}  # Adjust as needed


def license_complies_format(text):
    arabic_tunisia = r"[\u0600-\u06FF]+"
    pattern = rf'^\d{{1,4}}{arabic_tunisia}\d{{2,3}}$'
    pattern2 = rf'^[{arabic_tunisia}]\d{{1,8}}$'
    match1 = re.match(pattern, text)
    match2 = re.match(pattern2, text)
    if match1 :
        return 1
    elif match2:
        print(text)
        return 2
    else:
        return 0 

def format_license(text):
    license_plate_ = ''
    mapping = {
        0: dict_int_to_char, 
        1: dict_int_to_char, 
        2: dict_int_to_char,
        3: dict_int_to_char ,
        4: dict_char_to_int, 
        5: dict_char_to_int, 
        6: dict_char_to_int, 
        7: dict_char_to_int, 
        8: dict_int_to_char, 
        9: dict_int_to_char,
        10: dict_int_to_char
    }
    
    for j in range(len(text)):
        if j in mapping and text[j] in mapping[j]:
            license_plate_ += mapping[j][text[j]]
        else:
            license_plate_ += text[j]
    print(f"Formatted license plate: {license_plate_[8:]+license_plate_[4:7]+license_plate_[0:4]}")
    return license_plate_[8:]+license_plate_[4:7]+license_plate_[0:4]

def read_license_plate(license_plate_crop):
    detections = reader.readtext(license_plate_crop)
    for detection in detections:
        bbox, text, score = detection
        text = text.upper().replace(' ', '')
        text = text.upper().replace('.', '')
        text = text.upper().replace(':', '')
        text = text.upper().replace(',', '')
        text = text.upper().replace(']', '1')
        text = text.upper().replace('[', '1')
        text = text.upper().replace('ل', 'س')
        text = text.upper().replace('_', 'نت')
        if license_complies_format(text)==1:
            formatted_text = format_license(text)
            print(formatted_text)
            return formatted_text, score
        elif  license_complies_format(text)==2:
            formatted_text = text
            print(formatted_text)
            return formatted_text, score
            
    
    return None, None


def get_car(license_plate, vehicle_track_ids):
    x1, y1, x2, y2, score, class_id = license_plate
    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]
        if x1 > xcar1 and y1 > ycar1 and x2 < xcar2 and y2 < ycar2:
            return vehicle_track_ids[j]
    return -1, -1, -1, -1, -1