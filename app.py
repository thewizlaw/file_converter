from flask import Flask, request, render_template, send_from_directory, redirect
import pandas as pd
import os
import uuid
import tabula
import subprocess
import tempfile
from PIL import Image
import io



app = Flask(__name__, template_folder='templates', static_folder='static')



#########File Converter Project########
    
@app.route('/file-convert', methods=['POST'])
def file_convert():
    file = request.files.get('file')
    file_extension = file.filename.lower()
    file_type = request.form.get('filetype')
    
    if file_extension.endswith('.csv'):
        return convert_csv_file(file, file_type)
    elif file_extension.endswith('.xlsx'):
        return convert_excel_file(file, file_type)
    elif file_extension.endswith('.pdf'):
        return convert_pdf_file(file, file_type)
    elif file_extension.endswith('.webp') or file_extension.endswith('.jpg') or file_extension.endswith('.png'):
        return convert_image(file, file_type)
    else:
        return "Unsupported file type. Please upload a CSV, Excel, or PDF file."


def convert_csv_file(file, file_type):
    df = pd.read_csv(file)
    
    if file_type == 'excel':
        file_name = f'{uuid.uuid4()}.xlsx'
        df.to_excel(os.path.join('downloads', file_name))
        return render_template('downloads.html', file_name=file_name)
    elif file_type == 'html':
        file_name = f'{uuid.uuid4()}.html'
        df.to_html(os.path.join('downloads', file_name))
        return render_template('downloads.html', file_name=file_name)
    
def convert_excel_file(file, file_type):
    df = pd.read_excel(file, engine='openpyxl')
    
    if file_type == 'csv':
        file_name = f'{uuid.uuid4()}.csv'
        df.to_csv(os.path.join('downloads', file_name))
        return render_template('downloads.html', file_name=file_name)
    elif file_type == 'html':
        file_name = f'{uuid.uuid4()}.html'
        df.to_html(os.path.join('downloads', file_name))
        return render_template('downloads.html', file_name=file_name)
    
def convert_pdf_file(file, file_type):
    os.makedirs('uploads', exist_ok=True)
    temp_file_name = f'{uuid.uuid4()}.pdf'
    upload_path = os.path.join('uploads', temp_file_name)
    file.save(upload_path)
    
    dfs = tabula.read_pdf(upload_path, pages='all', multiple_tables=True)
    df = pd.concat(dfs)
    
    file_name = f'{uuid.uuid4()}.xlsx'
    df.to_excel(os.path.join('downloads', file_name))
    return render_template('downloads.html', file_name=file_name)

    
@app.route("/download_file/<filename>")
def download_file(filename):
    return send_from_directory('downloads', filename)

@app.route('/')
def file_converter_home():
    return render_template('home.html')



@app.route('/file-pandoc', methods=['POST'])
def file_pandoc():
    
    DOWNLOAD_FOLDER = 'downloads'
    
    file = request.files.get('file')
    target_format = request.form.get('filetype')
    filename = file.filename
    upload_path = os.path.join('uploads', filename)
    file.save(upload_path)
    
    tmp_fd, tmp_output = tempfile.mkstemp(suffix=f'.{target_format}')
    os.close(tmp_fd)
    
    try:
        subprocess.run(
            ['pandoc', upload_path, '-o', tmp_output], check=True
        )
    except subprocess.CalledProcessError as e:
        return f"Error converting file: {e}"
    
    output_filename = f"converted.{target_format}"
    output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
    return redirect(url_for('download_file', filename=output_filename))

def convert_image(file, target_format):
    
    img = Image.open(file.stream)
    
    output_filename = f"{uuid.uuid4()}.{target_format}"
    output_path = os.path.join('downloads', output_filename)
    
    img.save(output_path, format=target_format.upper())
    return render_template('downloads.html', file_name=output_filename)
    
@app.route('/image', methods=['POST', 'GET'])
def image_convert():
    return render_template('image.html')

if __name__ == '__main__':
    app.run(debug=True)
    