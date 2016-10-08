import cv2
import numpy
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color 
from colormath.color_diff import delta_e_cie2000
import urllib.request
import json

apiKey = "AIzaSyB8L4oW70lO2EAOUST2K6Oj1NtPJ1wnYow"
searchEngineID = "013516989698763720360:xmhvnomg9cu"
colors = {  "red"           :   [[255,      0,          0],     0],
            "orange"        :   [[255,      165,        0],     39],
            "yellow"        :   [[255,      255,        0],     60],
            "green"         :   [[0,        128,        0],     120],
            "blue"          :   [[0,        0,          255],   240],
            "purple"        :   [[128,      0,          128],   300],
            "brown"         :   [[165,      42,         42],    0],
            "pink"          :   [[255,      192,        203],   350],
            "white"         :   [[245,      245,        245],   0],
            "gray"          :   [[128,      128,        128],   0],
#            "light gray"    :   [[211,      211,        211],   0],
#            "dark gray"     :   [[169,      169,        169],   0],
            "black"         :   [[0,        0,          0],     0]
        }

def downloadImages():
    # cop pnk, gr, lg, dg, blk
    #colors.keys()
    for color in ["yellow"]:
        queryStart = 1
        imgCount = 0
        while imgCount < 49:
            searchURL = "https://www.googleapis.com/customsearch/v1?key=" + apiKey + "&cx=" + searchEngineID + "&q=" + color.replace(" ", "%20") + "%20color&searchType=image&start=" + str(queryStart)
            print(searchURL)
            rawData = urllib.request.urlopen(searchURL).read().decode("utf-8")
            itemList = json.loads(rawData)["items"]
            for j in range(len(itemList)):
                try:
                    urllib.request.urlretrieve(itemList[j]["link"], "images/" + color + "/" + str(imgCount) + "." +itemList[j]["link"].split(".")[-1])
                    print("success! \t\t " + str(imgCount) + "." +itemList[j]["link"].split(".")[-1])
                    imgCount += 1
                except Exception as e:
                    print(e)
                    print("fail! \t\t " + itemList[j]["link"])
            queryStart += 10

def peakHues(imgPath):
    bins = 180
    img = cv2.imread(imgPath)
    img = cv2.GaussianBlur(img, (7, 7), 0)
    img = cv2.pyrDown(img)
    img = cv2.pyrDown(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
    peaks = []
    for bin in range(bins):
        if (hist[bin][0] > hist[bin-1][0] and hist[bin][0] > hist[(bin+1)%bins][0]):
            peaks.append(bin*2) #change to 0 to 360 deg
    return peaks

def guessColorFromHues(imgPath):
    peaks = peakHues(imgPath)
    closestColors = []
    for peakHue in peaks:
        closestColor = "red"
        for color in colors:
            if (abs(peakHue - colors[color][1]) < abs(peakHue - colors[closestColor][1]) and color not in ["brown", "white", "gray", "light gray", "dark gray", "black"]):
                # avoid duplicate hues
                closestColor = color
        if closestColor not in closestColors: closestColors.append(closestColor)
    return closestColors

def guessColorFromLAB(imgPath):
    img = cv2.imread(imgPath)
    avgRow = numpy.average(img, axis = 0)
    avgColor = numpy.average(avgRow, axis = 0) # returns in bgr
    avgColor = numpy.uint8(avgColor)
    avgColor = [avgColor[2], avgColor[1], avgColor[0]]
    labAvg = convert_color(sRGBColor(avgColor[0]/255, avgColor[1]/255, avgColor[2]/255), LabColor)
    closestColor = "red"
    for color in colors:
        labColor = convert_color(sRGBColor(colors[color][0][0]/255, colors[color][0][1]/255, colors[color][0][2]/255), LabColor)
        labClosest = convert_color(sRGBColor(colors[closestColor][0][0]/255, colors[closestColor][0][1]/255, colors[closestColor][0][2]/255), LabColor)
        if (delta_e_cie2000(labAvg, labColor) < delta_e_cie2000(labAvg, labClosest)):
            closestColor = color
    return closestColor

def guessColor(imgPath):
    hueGuess = guessColorFromHues(imgPath)
    labGuess = guessColorFromLAB(imgPath)
    if labGuess in ["brown", "white", "gray", "black"]:
        return labGuess
    return hueGuess

#downloadImages()
#imgPath = "images/blue/1024px-Color_icon_blue.svg.png"
#print(guessColor(imgPath))