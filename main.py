from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.encoders import jsonable_encoder
import requests
import logging
import fitz
from casparser import read_cas_pdf

def identify_paragraphs(text):
    # Split text into paragraphs based on patterns or indicators specific to your PDFs
    # For simplicity, splitting by line breaks here
    paragraphs = text.split('\n\n')  # Adjust this logic based on the PDF's structure

    # Format identified paragraphs as HTML
    html_paragraphs = ""
    for paragraph in paragraphs:
        html_paragraphs += f"<p>{paragraph}</p>"

    return html_paragraphs

app = FastAPI()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/upload_cas/")
async def process_file(file: UploadFile = File(...), pan: str = Form(...), password: str = Form(...)):
    # Read CAS PDF and process data
    result = read_cas_pdf(file, pan, password)
    logger.info("Request Data: %s", result)
    # Convert result to JSON serializable format
    encoded_result = jsonable_encoder(result)
    # Log the internal API request data
    logger.info("Internal API Request Data: %s", encoded_result)

    # Make a POST request to the internal API
    url = 'https://mfapi.myvalidus.com/MF/Appcomfun/postEcasData'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=encoded_result, headers=headers)
    logger.info("Internal API Response Data: %s", response.text)
    if response.ok:
        return {"result": encoded_result}
    else:
        raise HTTPException(status_code=response.status_code, detail="Internal API call failed")


@app.post("/pdf_to_html/")
async def pdf_to_html(file: UploadFile = File(...)):
    try:
        # Read the uploaded file data
        pdf_data = await file.read()
        
        # Open the PDF with PyMuPDF
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        
        html_content = ""
        # Extract text and structure it as HTML content
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            html_content += f"<div class='page' id='page-{page_num + 1}'>"  # Create a div for each page

            # Extract paragraphs from text and format them as HTML
            extracted_text = page.get_text("text")
            extracted_paragraphs = identify_paragraphs(extracted_text)
            html_content += extracted_paragraphs

            html_content += "</div>"
        
        # Close the PDF document
        pdf_document.close()
        
        # Wrap the extracted content in HTML structure
        output_html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>PDF to HTML</title>
                <style>
                    .page {{
                        margin: 20px;
                        border: 1px solid #ccc;
                        padding: 10px;
                    }}
                    p {{
                        /* Your CSS styles for paragraphs */
                        /* Adjust according to your layout requirements */
                        margin-bottom: 10px; /* Example margin between paragraphs */
                        /* Additional styles as needed */
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
        '''

        return {"html_output": output_html}
    
    except Exception as e:
        return {"error": str(e)}