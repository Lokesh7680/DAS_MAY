from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
from PIL import Image
import io
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
 
def remove_background(signature_path):
    signature_img = Image.open(signature_path).convert("RGBA")
    data = signature_img.getdata()
    newData = []
    for item in data:
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    signature_img.putdata(newData)
    img_byte_array = io.BytesIO()
    signature_img.save(img_byte_array, format="PNG")
    img_byte_array.seek(0)
    return ImageReader(img_byte_array)
 
def place_signature_on_pdf(input_pdf_path, output_pdf_path, signature_path, coordinates, signature_size):
    signature_width, signature_height = signature_size
    transparent_signature = remove_background(signature_path)
    packet = canvas.Canvas("temp.pdf", pagesize=letter)
    packet.setPageSize(letter)
    packet.setFont("Helvetica", 10)
    packet.setFillColor(colors.red)
    packet.drawString(0, 0, "function showSerialNumber() {var serialNumber = document.getElementById('serialNumber'); serialNumber.style.visibility = 'visible';}")
    packet.drawString(0, 0, "function hideSerialNumber() {var serialNumber = document.getElementById('serialNumber'); serialNumber.style.visibility = 'hidden';}")
    with open(input_pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_width = float(page.mediabox.upper_right[0])
            page_height = float(page.mediabox.upper_right[1])
            packet.setPageSize((page_width, page_height))
            for index, (x, y) in enumerate(coordinates, start=1):
                x = float(x)
                y = float(y)
                y = page_height - y
                packet.drawImage(transparent_signature, x, y, width=signature_width, height=signature_height)
                packet.drawString(x, y - 20, str(index))
                packet.linkRect("", "javascript:showSerialNumber();", (x, y, x + signature_width, y + signature_height), "URI")
                packet.linkRect("", "javascript:hideSerialNumber();", (x, y, x + signature_width, y + signature_height), "URI")
                packet.drawString(x + 5, y - 5, str(index))
            packet.showPage()
    packet.save()
    temp_pdf = PyPDF2.PdfReader("temp.pdf")
    input_pdf = PyPDF2.PdfReader(input_pdf_path)
    output = PyPDF2.PdfWriter()
    for i in range(len(input_pdf.pages)):
        input_page = input_pdf.pages[i]
        temp_page = temp_pdf.pages[i]
        input_page.merge_page(temp_page)
        output.add_page(input_page)
    with open(output_pdf_path, 'wb') as output_file:
        output.write(output_file)
    print("Serial numbers placed correctly!")
 
# Example usage
input_pdf_path = 'C:\\Users\\LENOVO\\Documents\\dax\\new\\ai.pdf'
output_pdf_path = 'C:\\Users\\LENOVO\\Documents\\dax\\input\\New\\orange.pdf'
signature_path = 'C:\\Users\\LENOVO\\Documents\\position\\sign5.png'
coordinates = [(270.00, 444.00), (52, 445)]
signature_size = (60, 25)
place_signature_on_pdf(input_pdf_path, output_pdf_path, signature_path, coordinates, signature_size)