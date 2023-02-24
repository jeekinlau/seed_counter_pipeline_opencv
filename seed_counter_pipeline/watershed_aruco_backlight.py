# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 11:30:53 2023

@author: jeeki
"""
import imutils
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from imutils.perspective import four_point_transform
import cv2
import numpy as np
from scipy import ndimage

# define a resizing function
def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)


def show(image,x=30,y=7):
  img=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  plt.figure(figsize=(x,y))
  plt.imshow(img)

image = cv2.imread("temp.jpg")
image = cv2.rotate(image,cv2.ROTATE_180)

#cv2.imshow("thresh",image)
#cv2.waitKey(0)



# Load image, grayscale, Gaussian blur, Otsu's thresho
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5,5), 0)
thresh = cv2.threshold(blur, 175, 255, cv2.THRESH_BINARY )[1]
thresh = cv2.bitwise_not(thresh)

#cv2.imshow("thresh",thresh)
#cv2.waitKey(0)




# Find contours and sort for largest contour
cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
displayCnt = None

for c in cnts:
    # Perform contour approximation
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    if len(approx) == 4:
        displayCnt = approx
        break



# Obtain birds' eye view of image
warped = four_point_transform(image, displayCnt.reshape(4, 2))

dim=(int(3000),int(2250))

warped_resize = cv2.resize(warped, dim, interpolation = cv2.INTER_AREA)


percent=0.01
cropped=warped_resize[int(len(warped_resize)*percent):int(len(warped_resize)*(1-percent)), int(len(warped_resize[0])*percent):int(len(warped_resize[0])*(1-percent))]

resize = ResizeWithAspectRatio(cropped, width=3000)


cv2.imwrite("trimmed.jpg", resize)


image = cv2.imread("trimmed.jpg")
#image = cv2.rotate(image,cv2.ROTATE_180)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5,5), 0)

thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]



arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
arucoParams = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(image)

detected=cv2.aruco.drawDetectedMarkers(image,markerCorners, markerIds)


#show(detected)

#cv2.imshow("Thresh", ResizeWithAspectRatio(detected,width=1000))
#cv2.waitKey(0)

aruco_areas=[]
for area in markerCorners: 
    aruco_areas.append(cv2.contourArea(area))


for rect in markerCorners:
    x,y,w,h =cv2.boundingRect(rect)
    w=w+5
    h=h+5
    cv2.rectangle(thresh,(x-5,y-5),(x+w,y+h),(255,255,),-1)
    
#cv2.imshow("result", ResizeWithAspectRatio(thresh,width=1000))
#cv2.waitKey(0)

thresh=cv2.bitwise_not(thresh)

# Noise removal
#kernel = np.ones((3),np.uint8)
#clear_image = cv2.morphologyEx(thresh,cv2.MORPH_OPEN, kernel, iterations=5)


#show(clear_image)
#cv2.imshow("Thresh", ResizeWithAspectRatio(thresh,width=1000))
#cv2.waitKey(0)

#thresh = clear_image
# compute the exact Euclidean distance from every binary
# pixel to the nearest zero pixel, then find peaks in this
# distance map
D = ndimage.distance_transform_edt(thresh)
localMax = peak_local_max(D, indices=False, min_distance=15, labels=thresh)
# perform a connected component analysis on the local peaks,
# using 8-connectivity, then appy the Watershed algorithm
markers = ndimage.label(localMax, structure=np.ones((3, 3)))[0]
labels = watershed(-D, markers, mask=thresh)

#print("[INFO] {} unique segments found".format(len(np.unique(labels)) - 1))


# isolate the small ones and remove

dust_thresh = 100.0

area=[]
rejected=[]
# loop over the unique labels returned by the Watershed
# algorithm
for label in np.unique(labels):
    # if the label is zero, we are examining the 'background'
    # so simply ignore it
    if label == 0:
        continue
    # otherwise, allocate memory for the label region and draw
    # it on the mask
    mask = np.zeros(gray.shape, dtype="uint8")
    mask[labels == label] = 255
    # detect contours in the mask and grab the largest one
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) > dust_thresh:
        area.append(cv2.contourArea(c))
        # draw a circle enclosing the object
        ((x, y), r) = cv2.minEnclosingCircle(c)
        cv2.circle(image, (int(x), int(y)), int(1), (0, 0, 255), 10)
        #cv2.putText(image, "#{}".format(label), (int(x) - 10, int(y)),
        #    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    if cv2.contourArea(c) < dust_thresh:
        rejected.append(cv2.contourArea(c))   


# show the output image
#cv2.imshow("Output", ResizeWithAspectRatio(image,width=1000))
#cv2.waitKey(0)
cv2.imwrite("contours.jpg",image)


print("[INFO] {} unique segments found".format(len(area)))

area_sort = np.sort(area)[::-1]
square_irl = 12.7**2.0
temp_mm=area_sort * square_irl / np.average(aruco_areas[0:4])
final=np.column_stack((area,temp_mm))


print("average size of objects is {} mm\u00b2" .format(np.average(temp_mm)))
np.savetxt("area_mm.csv", final, delimiter=",", fmt='%f')

