from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from app.services.email_service import send_email, send_otp_to_signer
from app.utils.auth_utils import generate_temp_password
from datetime import datetime, timedelta
import hashlib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
from PIL import Image

app = FastAPI()

# mongo_uri = os.getenv("MONGO_URI")
# mongo_uri = "mongodb+srv://yosuvaberry:yosuvaberry@cluster0.mnf3k57.mongodb.net/?retryWrites=true&w=majority"
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']

def find_next_signer(document, current_signer_id):
    signers = sorted(document.get('signers', []), key=lambda x: x.get('order', 0))  # Handle missing 'order' key
    current_index = next((i for i, s in enumerate(signers) if s['signer_id'] == current_signer_id), None)

    if current_index is not None and current_index + 1 < len(signers):
        return signers[current_index + 1]

    return None

def initiate_signing_for_signer(document_id, signer_id):
    # Fetch the document and find the specific signer   
    document = db.documents.find_one({"document_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    signer = next((s for s in document['signers'] if s['signer_id'] == signer_id), None)
    print(signer)
    if not signer:
        raise HTTPException(status_code=404, detail="Signer not found")

    # Generate a temporary password
    temp_password = generate_temp_password()
    hash_pass = hashlib.sha256(temp_password.encode()).hexdigest()
    password_expiration = datetime.now() + timedelta(days=5)

    # Store the credentials
    db.users.insert_one({
        "email": signer['email'],
        "phone_number": signer['phone_number'],
        "signer_id": signer['signer_id'],
        "roles": ["signer"],
        "password": hash_pass,
        "expiration": password_expiration
    })
    signer_email= signer['email']
    # Send email to the signer
    email_body = f"Dear Signer,\n\nYou have been granted access to sign a document. Below are your credentials:\n\nUsername: {signer_email}\nTemporary Password: {temp_password}\n\nPlease use the provided credentials to log in and complete the signing process. Ensure to keep your password confidential for security purposes.\n\nIf you have any questions or encounter any issues, please don't hesitate to contact us for assistance.\n\nBest regards,\n[Your Name]\n[Your Position/Title]\n[Your Contact Information]"
    print(signer)
    send_email(signer['email'], "Document Signing Credentials", email_body)

    return "Email sent to the signer"

def send_email_to_signer(signer_id, message):
    print(signer_id)
    # Fetch signer's details from the database
    # signer = db.users.find_one({"email": signer_id})
    signer = db.users.find_one({"signer_id": signer_id})
    print(signer)
    if signer:
        email = signer.get('email')
        if email:
            subject = "Document Signing Update"
            send_email(email, subject, message)

        else:
            print("Email address not found for signer.")
    else:
        print("Signer not found in the database.")

def send_email_to_admin(admin_id, message):
    # Fetch admin's details from the database
    admin = db.users.find_one({"admin_id": admin_id})
    if admin:
        email = admin.get('email')
        if email:
            subject = "Document Signing Status"
            send_email(email, subject, message)
        else:
            print("Email address not found for admin.")
    else:
        print("Admin not found in the database.")

def send_email_to_individual(individual_id, message):
    # Fetch admin's details from the database
    admin = db.users.find_one({"individual_id": individual_id})
    if admin:
        email = admin.get('email')
        if email:
            subject = "Document Signing Status"
            send_email(email, subject, message)
        else:
            print("Email address not found for admin.")
    else:
        print("Admin not found in the database.")

def validate_signer_document_requirements(document, signer_document):
    print("signer_document :", signer_document)
    print("document :", document)
    for signer in document.get('signers', []):
        if signer.get('signer_id') == signer_document.get('signer_id'):
            options = dict(signer.get('options', {}))
            print("options:", options)
            print("signer_document:", signer_document)
            results = {
                'photo': options.get('photo', False) == ('photo' in signer_document),
                'video': options.get('video', False) == ('video' in signer_document),
                'govt_id': options.get('govt_id', False) == ('govt_id' in signer_document),
                'signature': options.get('signature', False) == ('signature' in signer_document)
            }
            print("results:", results)
            validation_result = all(results.values())
            print("validation_result:", validation_result)
            return validation_result
    return False

# def make_transparent_background(signature_path):
#     # Open signature image
#     signature_img = Image.open(signature_path).convert("RGBA")
   
#     # Get pixel data
#     data = signature_img.getdata()
 
#     # Convert to list of pixels
#     newData = []
#     for item in data:
#         # Change all white (also shades of whites)
#         # pixels to transparent
#         if item[0] > 200 and item[1] > 200 and item[2] > 200:
#             newData.append((255, 255, 255, 0))
#         else:
#             newData.append(item)
   
#     # Update image data
#     signature_img.putdata(newData)
   
#     # Save image with transparent background
#     transparent_path = "signature_transparent.png"
#     signature_img.save(transparent_path, "PNG")
   
#     return transparent_path
 
# def place_signature_on_pdf(input_pdf_path, output_pdf_path, signature_path, coordinates):
#     transparent_path = make_transparent_background(signature_path)
   
#     packet = canvas.Canvas("temp.pdf", pagesize=letter)
 
#     with open(input_pdf_path, 'rb') as file:
#         reader = PyPDF2.PdfReader(file)
 
#         for page_num in range(len(reader.pages)):
#             page = reader.pages[page_num]
#             page_width = float(page.mediabox.upper_right[0])
#             page_height = float(page.mediabox.upper_right[1])
 
#             packet.setPageSize((page_width, page_height))
 
#             for x, y in coordinates:
#                 x = float(x)
#                 y = float(y)  # Convert y to float
 
#                 # Convert PDF y-coordinate to Python coordinate system
#                 y = page_height - y
 
#                 # Use transparent signature image
#                 packet.drawImage(transparent_path, x, y, width=100, height=50)
 
#             packet.showPage()
 
#     packet.save()
 
#     # Merge temp.pdf with input PDF
#     temp_pdf = PyPDF2.PdfReader("temp.pdf")
#     input_pdf = PyPDF2.PdfReader(input_pdf_path)
 
#     output = PyPDF2.PdfWriter()
 
#     for i in range(len(input_pdf.pages)):
#         input_page = input_pdf.pages[i]
#         temp_page = temp_pdf.pages[i]
       
#         input_page.merge_page(temp_page)
#         output.add_page(input_page)
 
#     with open(output_pdf_path, 'wb') as output_file:
#         output.write(output_file)

# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# import PyPDF2
# from PIL import Image
 
# def make_transparent_background(signature_path):
#     # Open signature image
#     signature_img = Image.open(signature_path).convert("RGBA")
   
#     # Get pixel data
#     data = signature_img.getdata()
 
#     # Convert to list of pixels
#     newData = []
#     for item in data:
#         # Change all white (also shades of whites)
#         # pixels to transparent
#         if item[0] > 200 and item[1] > 200 and item[2] > 200:
#             newData.append((255, 255, 255, 0))
#         else:
#             newData.append(item)
   
#     # Update image data
#     signature_img.putdata(newData)
   
#     # Save image with transparent background
#     transparent_path = "signature_transparent.png"
#     signature_img.save(transparent_path, "PNG")
   
#     return transparent_path
 
# def place_signature_on_pdf(signer_id, signature_size):
#     # Retrieve input parameters from the database
#     document_record = db.documents.find_one({"signer_id": signer_id})
#     input_pdf_path = document_record["document_path"]
#     coordinates = document_record["coordinates"]

#     signature_record = db.signerdocuments.find_one({"signer_id": signer_id})
#     signature_path = signature_record["signature_path"]
#     output_pdf_path = signature_record.get("output_pdf_path", "C:\\output\\{signer_id}.pdf")  # Default output path if not present

#     # Signature width and height from the provided signature size
#     signature_width, signature_height = signature_size

#     # Generate transparent background for the signature
#     transparent_path = make_transparent_background(signature_path)

#     # Create a canvas for the PDF
#     packet = canvas.Canvas("temp.pdf", pagesize=letter)

#     # Open the input PDF file
#     with open(input_pdf_path, 'rb') as file:
#         reader = PyPDF2.PdfReader(file)

#         # Iterate through pages in the input PDF
#         for page_num in range(len(reader.pages)):
#             page = reader.pages[page_num]
#             page_width = float(page.mediabox.upper_right[0])
#             page_height = float(page.mediabox.upper_right[1])

#             # Set the page size for the canvas
#             packet.setPageSize((page_width, page_height))

#             # Iterate through coordinates and place the signature on each page
#             for x, y in coordinates:
#                 x = float(x)
#                 y = float(y)  # Convert y to float

#                 # Convert PDF y-coordinate to Python coordinate system
#                 y = page_height - y

#                 # Use transparent signature image with specified width and height
#                 packet.drawImage(transparent_path, x, y, width=signature_width, height=signature_height)

#             # Show the page in the canvas
#             packet.showPage()

#     # Save the canvas as temporary PDF
#     packet.save()

#     # Merge temporary PDF with input PDF
#     temp_pdf = PyPDF2.PdfReader("temp.pdf")
#     input_pdf = PyPDF2.PdfReader(input_pdf_path)

#     output = PyPDF2.PdfWriter()

#     for i in range(len(input_pdf.pages)):
#         input_page = input_pdf.pages[i]
#         temp_page = temp_pdf.pages[i]

#         input_page.merge_page(temp_page)
#         output.add_page(input_page)

#     # Write the output PDF file
#     with open(output_pdf_path, 'wb') as output_file:
#         output.write(output_file)


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
from PIL import Image
import io
from reportlab.lib.utils import ImageReader
import base64
 
# def remove_background(signature_img):
#     # Open signature image
#     signature_img = Image.open(io.BytesIO(signature_img)).convert("RGBA")
#     # Get pixel data
#     data = signature_img.getdata()
#     # Convert to list of pixels
#     newData = []
#     for item in data:
#         # Change all white (also shades of whites)
#         # pixels to transparent
#         if item[0] > 200 and item[1] > 200 and item[2] > 200:
#             newData.append((255, 255, 255, 0))  # Set alpha to 0 for white pixels
#         else:
#             newData.append(item)
#     # Update image data
#     signature_img.putdata(newData)
#     # Convert PIL image to bytes
#     img_byte_array = io.BytesIO()
#     signature_img.save(img_byte_array, format="PNG")
#     img_byte_array.seek(0)
#     # Convert BytesIO to ImageReader
#     return ImageReader(img_byte_array)
 
# def place_signature_on_pdf(input_pdf_base64, signature_base64, coordinates, signature_size):
#     signature_width, signature_height = signature_size
#     transparent_signature = remove_background(base64.b64decode(signature_base64))
#     packet = io.BytesIO()
#     input_pdf_data = base64.b64decode(input_pdf_base64)
#     reader = PyPDF2.PdfReader(io.BytesIO(input_pdf_data))
#     writer = PyPDF2.PdfWriter()
#     for page_num in range(len(reader.pages)):
#         page = reader.pages[page_num]
#         page_width = float(page.mediabox.upper_right[0])
#         page_height = float(page.mediabox.upper_right[1])
#         packet = io.BytesIO()
#         packet_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
#         for x, y in coordinates:
#             x = float(x)
#             y = float(y)  # Convert y to float
#             # Convert PDF y-coordinate to Python coordinate system
#             y = page_height - y
#             # Use transparent signature image with specified width and height
#             packet_canvas.drawImage(transparent_signature, x, y, width=signature_width, height=signature_height)
#         packet_canvas.save()
#         packet.seek(0)
#         new_pdf = PyPDF2.PdfReader(packet)
#         writer.add_page(new_pdf.pages[0])
#     output_pdf = io.BytesIO()
#     writer.write(output_pdf)
#     output_pdf.seek(0)
#     return base64.b64encode(output_pdf.getvalue()).decode()

# ---------------------------------------

# def remove_background(signature_img):
#     signature_img = Image.open(io.BytesIO(signature_img)).convert("RGBA")
#     data = signature_img.getdata()
#     newData = []
#     for item in data:
#         if item[0] > 200 and item[1] > 200 and item[2] > 200:
#             newData.append((255, 255, 255, 0))
#         else:
#             newData.append(item)
#     signature_img.putdata(newData)
#     img_byte_array = io.BytesIO()
#     signature_img.save(img_byte_array, format="PNG")
#     img_byte_array.seek(0)
#     return Image.open(img_byte_array)
 
# def place_signature_on_pdf(input_base64, signature_base64, coordinates, signature_size):
#     signature_width, signature_height = signature_size
#     signature_png_bytes = base64.b64decode(signature_base64)
#     transparent_signature = remove_background(signature_png_bytes)
#     reader = PyPDF2.PdfReader(io.BytesIO(base64.b64decode(input_base64)))
#     writer = PyPDF2.PdfWriter()
#     for page_num in range(len(reader.pages)):
#         page = reader.pages[page_num]
#         page_width = float(page.mediabox.upper_right[0])
#         page_height = float(page.mediabox.upper_right[1])
#         packet = io.BytesIO()
#         packet_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
#         for x, y in coordinates:
#             x = float(x)
#             y = float(y)
#             y = page_height - y
#             packet_canvas.drawImage(transparent_signature, x, y, width=signature_width, height=signature_height)
#         packet_canvas.save()
#         packet.seek(0)
#         new_doc = PyPDF2.PdfReader(packet)
#         writer.add_page(new_doc.pages[0])
#     output_doc = io.BytesIO()
#     writer.write(output_doc)
#     output_doc.seek(0)
#     return base64.b64encode(output_doc.getvalue()).decode()

# -----------------------------------

import cv2
import numpy as np
from PIL import Image
import io
import base64
import PyPDF2
from reportlab.pdfgen import canvas

def remove_background(signature_base64):
    # Decode base64 string to image data
    signature_data = base64.b64decode(signature_base64)
    signature_np_array = np.frombuffer(signature_data, np.uint8)
    signature_img = cv2.imdecode(signature_np_array, cv2.IMREAD_GRAYSCALE)
    
    # Define a threshold to convert image to binary
    thresh = 110
    signature_img_binary = cv2.threshold(signature_img, thresh, 255, cv2.THRESH_BINARY)[1]
    
    # Convert numpy array to PIL Image
    signature_img_pil = Image.fromarray(signature_img_binary)
    signature_img_pil = signature_img_pil.convert("RGBA")
    
    # Access pixel data
    pixdata = signature_img_pil.load()
    
    # Iterate over each pixel and change fully opaque white pixels to transparent
    width, height = signature_img_pil.size
    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == (255, 255, 255, 255):  # Transparent white
                pixdata[x, y] = (255, 255, 255, 0)  # Set to transparent
    
    # Save the modified image to a buffer as PNG format
    output_buffer = io.BytesIO()
    signature_img_pil.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    
    # Get the base64 encoded string of the modified image
    base64_output_string = base64.b64encode(output_buffer.getvalue()).decode()

    # db.signerdocuments.update_one(
    # {"signer_id": signer_id, "document_id": document_id},
    # {"$set": {"base64_output_string":base64_output_string}},
    # upsert=True
    # )

    return base64_output_string

def place_signature_on_pdf(input_base64, signature_base64, coordinates, signature_size):
    signature_width, signature_height = signature_size
    
    # Get transparent signature image
    transparent_signature_base64 = remove_background(signature_base64)

    # Proceed with PDF processing (same as before)
    reader = PyPDF2.PdfReader(io.BytesIO(base64.b64decode(input_base64)))
    writer = PyPDF2.PdfWriter()
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page_width = float(page.mediabox.upper_right[0])
        page_height = float(page.mediabox.upper_right[1])
        
        packet = io.BytesIO()
        packet_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        for x, y in coordinates:
            x = float(x)
            y = float(y)
            y = page_height - y  # Flip y-coordinate for PDF coordinate system
            transparent_signature_img = Image.open(io.BytesIO(base64.b64decode(transparent_signature_base64)))
            packet_canvas.drawImage(transparent_signature_img, x, y, width=signature_width, height=signature_height)
        
        packet_canvas.save()
        packet.seek(0)
        
        new_doc = PyPDF2.PdfReader(packet)
        writer.add_page(new_doc.pages[0])
    
    output_doc = io.BytesIO()
    writer.write(output_doc)
    output_doc.seek(0)
    
    # Get the base64 encoded string of the resulting PDF
    resulting_pdf_base64 = base64.b64encode(output_doc.getvalue()).decode()
    
    return resulting_pdf_base64