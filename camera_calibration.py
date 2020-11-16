import cv2
from cv2 import aruco
import numpy as np
import yaml
from pathlib import Path
from tqdm import tqdm

def inverse_pose(rotation_vector, translation_vector):
    rotation_matrix, jacobian = cv2.Rodrigues(rotation_vector)
    rotation_matrix = numpy.matrix(rotation_matrix).T

    inverse_rotation_vector, jacobian = cv2.Rodrigues(rotation_matrix)
    inverse_translation_vector = numpy.dot(-rotation_matrix, numpy.matrix(translation_vector))

    return inverse_rotation_vector, inverse_translation_vector


def relative_pose(rotation_vector_parent, translation_vector_parent, rotation_vector_child, translation_vector_child):
    rotation_vector_parent, translation_vector_parent = rotation_vector_parent.reshape((3, 1)), translation_vector_parent.reshape((3, 1))
    rotation_vector_child, translation_vector_child = rotation_vector_child.reshape((3, 1)), translation_vector_child.reshape((3, 1))

    inverse_rotation_vector_child, inverse_translation_vector_child = inverse_pose(rotation_vector_child, translation_vector_child)

    composed_matrix = cv2.composeRT(rotation_vector_parent, translation_vector_parent, inverse_rotation_vector_child, inverse_translation_vector_child)
    composed_rotation_vector = composed_matrix[0]
    composed_translation_vector = composed_matrix[1]

    composed_rotation_vector.reshape((3, 1))
    composed_translation_vector. reshape((3, 1))

    return composed_rotation_vector, composed_translation_vector


# root directory of repo for relative path specification.
root = Path(__file__).parent.absolute()

# Set this flsg True for calibrating camera and False for validating results real time
calibrate_camera = True

# Set path to the images
calib_imgs_path = root.joinpath("aruco_data")

# For validating results, show aruco board to camera.
aruco_dict = aruco.getPredefinedDictionary( aruco.DICT_6X6_1000 )

#Provide length of the marker's side
markerLength = 3.75  # Here, measurement unit is centimeters.

# Provide separation between markers
markerSeparation = 0.5   # Here, measurement unit is centimeters.

# create arUco board
board = aruco.GridBoard_create(4, 5, markerLength, markerSeparation, aruco_dict)

# create parameters
arucoParams = aruco.DetectorParameters_create()

if calibrate_camera == True:
    img_list = []
    # find all images with ending jpg
    calib_fnms = calib_imgs_path.glob('*.jpg')
    # print('Using ...', end='')
    for idx, fn in enumerate(calib_fnms):
        #print(idx, '', end='')
        img = cv2.imread( str(root.joinpath(fn) ))
        img_list.append( img )
        h, w, c = img.shape
    print('Calibration images')

    counter, corners_list, id_list = [], [], []
    first = True
    # added tqdm
    for im in tqdm(img_list):
        img_gray = cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
        corners, ids, rejectedImgPoints = aruco.detectMarkers(img_gray, aruco_dict, parameters=arucoParams)
        if first == True:
            corners_list = corners
            id_list = ids
            first = False
        else:
            corners_list = np.vstack((corners_list, corners))
            id_list = np.vstack((id_list,ids))
        counter.append(len(ids))
    print('Found {} unique markers'.format(np.unique(ids)))

    counter = np.array(counter)
    #mat = np.zeros((3,3), float)
    ret, mtx, dist, rvecs, tvecs = aruco.calibrateCameraAruco(corners_list, id_list, counter, board, img_gray.shape, None, None )

    print("Camera matrix is \n", mtx, "\n And is stored in calibration.yaml file along with distortion coefficients : \n", dist)
    data = {'camera_matrix': np.asarray(mtx).tolist(), 'dist_coeff': np.asarray(dist).tolist()}
    with open("calibration.yaml", "w") as f:
        yaml.dump(data, f)


# change to vid on your directory
cap = cv2.VideoCapture("/Users/mokakoba/agisoft/agisoftscan/camera_calibration-master/test_aruco.mov")

while (True):
    datalist = []
    count = 0
    ret, frame = cap.read()
   
    # operations on the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # set dictionary size depending on the aruco marker selected
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)

    # detector parameters can be set here (List of detection parameters[3])
    parameters = aruco.DetectorParameters_create()
    parameters.adaptiveThreshConstant = 10

    # lists of ids and the corners belonging to each id
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # font for displaying text (below)
    font = cv2.FONT_HERSHEY_SIMPLEX

    # check if the ids list is not empty
    # if no check is added the code will crash
    if np.all(ids != None):

        # estimate pose of each marker and return the values
        # rvet and tvec-different from camera coefficients
        rvec, tvec , _ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist)
        data = {'rvec': np.asarray(rvec).tolist(), 'tvec': np.asarray(tvec).tolist()}
        with open("pose_estimation"+".yaml", "w") as w:
            yaml.dump(data, w)
        
        for i in range(0, ids.size):
            # draw axis for the aruco markers
            aruco.drawAxis(frame, mtx, dist, rvec[i], tvec[i], 0.1)
        
        # draw a square around the markers
        aruco.drawDetectedMarkers(frame, corners)

        # code to show ids of the marker found
        strg = ''
        for i in range(0, ids.size):
            strg += str(ids[i][0])+', '

        cv2.putText(frame, "Id: " + strg, (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)

    else:
        # code to show 'No Ids' when no markers are found
        cv2.putText(frame, "No Ids", (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)

    # display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



