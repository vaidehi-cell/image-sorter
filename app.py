from flask import *
import os
from werkzeug.utils import secure_filename
import cv2
import shutil

# Declare paths for the folders where input images and output images (clear and blurred) will be stored
UPLOAD_FOLDER = 'image_upload'
BLURRED = 'blurred'
CLEAR = 'clear'

# Define the app
app = Flask(__name__)
app.secret_key = "nisargee"
# Configure the folder paths for the app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BLURRED'] = BLURRED
app.config['CLEAR'] = CLEAR

# List of allowed extensions of files
ALLOWED_EXTENSIONS = {'bmp', 'dib', 'jpeg', 'jpg', 'jpe', 'jp2', 'png', 'webp', 'pbm', 'pgm','ppm', 'pxm', 'pnm', 'pfm', 'sr', 'ras', 'tiff', 'tif', 'exr', 'hdr', 'pic'}


'''Utility functions'''

# Utility function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility function to check if the file is a zip archive file
def is_compressed(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'zip'

# Delete all the input images, clear and blurred images from the respective folders
def clear_folders():
    # Clear all the input images
    preExistingFiles = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    for filename in preExistingFiles:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # Clear all the blurred images
    preExistingFiles = [f for f in os.listdir(app.config['BLURRED']) if os.path.isfile(os.path.join(app.config['BLURRED'], f))]
    for filename in preExistingFiles:
        os.remove(os.path.join(app.config['BLURRED'], filename))  
    
    # Clear all the clear images
    preExistingFiles = [f for f in os.listdir(app.config['CLEAR']) if os.path.isfile(os.path.join(app.config['CLEAR'], f))]
    for filename in preExistingFiles:
        os.remove(os.path.join(app.config['CLEAR'], filename))  
    
    # Clear all the zip files
    preExistingFiles = [f for f in os.listdir(app.root_path) if os.path.isfile(f) and is_compressed(f)]
    for filename in preExistingFiles:
        os.remove(os.path.join(app.root_path, filename))

'''Views are defined below'''

# Default path where home page will be loaded
@app.route('/')
def index():
    return render_template('index.html')

# Submit the image folder for processing and seperate images into blurred and clear folder
@app.route('/submit', methods = ["POST", "GET"])
def submit():
    # if the request method is post, i.e, the input is submitted
    try:
        if request.method == "POST":
            # if required input is not found
            if 'ctrl' not in request.files:
                # Show a flash message and redirect to the same page
                flash('No file part')
                return redirect(request.url)
            else:
                data = request.files.getlist('ctrl')
                flash('got the files')
                # If user has entered a valid threshold, use it else set threshold to default value 81
                try:
                    threshold = int(request.form['threshold'])
                except:
                    threshold = 81
                flash('set the threshold')
                # cLear all the pre-existing files: to minimise the amount of data stored at the server
                clear_folders()  
                flash('cleared folders')
                # iterate through the input files
                for file in data:
                    
                    # check if valid file, save it
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    # if file invalid, return error message
                    else:
                        return render_template('index.html', download = False, message='Invalid file format!')
                flash('saved files')
                # iterate through the input images
                for file in data:
                    filename = secure_filename(file.filename)

                    # read file as image using cv2
                    image = cv2.imread(app.config['UPLOAD_FOLDER'] +'\\'+ filename)
                    flash('took image in opencv')
                    # convert into grayscale image
                    imagebw = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    flash('converted to greyscale')
                    # finds focus measure of the image
                    ''' Focus measure is the degree of sharpness of an image i.e., so higher focus measure, more clear image.
                    Focus measure is calculated by finding gradient of gaussian filter or a laplacian filter on an image. 
                    Here, we use Laplacian filter. '''
                    focus_measure = cv2.Laplacian(imagebw, cv2.CV_64F).var() 
                    flash('calculated focus measure')
                    # If focus measure < threshold, the image is blur, so save in blurred folder
                    if focus_measure < threshold: 
                        cv2.imwrite('./blurred/' + filename, image) 
                        
                    # If focus measure >= threshold, the image is clear, so save in clear folder
                    else:
                        cv2.imwrite('./clear/' + filename, image) 
                    flash('saved images')
            # Return the home page with download option allowed 
            return render_template('index.html', download = True)
        else:
            
            # Return the home page with download option not allowed 
            return render_template('index.html', download = False)
    except Exception as e:
        flash(e)
        return render_template('index.html', download = False)
# Download processed blur images
@app.route('/download_blur', methods = ["POST", "GET"])
def download_blur():

    # if the request method is post, do not allow download
    if request.method == 'POST':
        return render_template('index.html', download = False)

    # if the request method is GET
    else:
        dir_name = os.path.join(app.root_path, app.config['BLURRED'])

        # Make a zip archive of blurred folder
        shutil.make_archive(dir_name, 'zip', dir_name)
        flash('zipped folder')
        # Download zip archive of blurred folder
        return send_file(dir_name + '.zip', as_attachment = True)

# Download processed clear images
@app.route('/download_clear', methods = ["POST", "GET"])
def download_clear():

    # if the request method is post, do not allow download
    if request.method == 'POST':
        return render_template('index.html', download = False)

    # if the request method is GET
    else:
        dir_name = os.path.join(app.root_path, app.config['CLEAR'])

        # Make a zip archive of clear folder
        shutil.make_archive(dir_name, 'zip', dir_name)
        flash('zipped folder')
        # Download zip archive of clear folder
        return send_file(dir_name + '.zip', as_attachment = True)

if __name__== "__main__":
    app.run(host='0.0.0.0',port=8080)
