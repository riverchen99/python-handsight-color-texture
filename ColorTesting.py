import cv2
import numpy
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color 
from colormath.color_diff import delta_e_cie2000
import urllib.request
import json
import os

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
            "black"         :   [[0,        0,          0],     0]
        }

# from xkcd color survey
colors =  { "red"           :   [[229,      0,          0],     0],
            "orange"        :   [[249,      115,        6],     26.91],
            "yellow"        :   [[255,      255,        20],    60],
            "green"         :   [[21,       176,        26],    121.94],
            "blue"          :   [[3,        67,         223],   222.55],
            "purple"        :   [[126,      30,         156],   285.71],
            "brown"         :   [[101,      55,         0],     32],
            "pink"          :   [[255,      129,        192],   330],
            "white"         :   [[255,      255,        255],   0],
            "gray"          :   [[146,      149,        145],   105], #misleading, actually green hue
            "black"         :   [[0,        0,          0],     0]
        }

def generateImageSet():
    #double color solution fail
    for color in colors.keys():
        try:
            os.makedirs("images/" + color + " color")
        except:
            pass
        downloadImages(color + " color")

def downloadImages(query):
    queryStart = 1
    imgCount = 0
    while imgCount < 50:
            searchURL = "https://www.googleapis.com/customsearch/v1?searchType=image&key=%s&cx=%s&q=%s&start=%s" % (apiKey, searchEngineID, query.replace(" ", "%20"), str(queryStart))
            rawData = urllib.request.urlopen(urllib.request.Request(searchURL, headers={"User-Agent" : "Magic Browser"})).read().decode("utf-8")
            itemList = json.loads(rawData)["items"]
            for j in range(len(itemList)):
                try:
                    urllib.request.urlretrieve(itemList[j]["link"], "images/%s/%s.%s" % (query, str(imgCount), itemList[j]["link"].split(".")[-1]))
                    print("success! \t\t %s.%s" % (str(imgCount), itemList[j]["link"].split(".")[-1]))
                    imgCount += 1
                except Exception as e:
                    print(e)
                    print("fail! \t\t " + itemList[j]["link"])
            queryStart += 10

def peakHues(img):
    bins = 180
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

def guessColorFromHues(img):
    peaks = peakHues(img)
    closestColors = []
    for peakHue in peaks:
        closestColor = "red"
        for color in colors:
            if (abs(peakHue - colors[color][1]) < abs(peakHue - colors[closestColor][1]) and color not in ["white", "gray", "black"]):
                # avoid duplicate hues
                closestColor = color
        if closestColor not in closestColors: closestColors.append(closestColor)
    return closestColors

def guessColorFromLAB(img):
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

def guessColor(img):
    hueGuess = guessColorFromHues(img)
    labGuess = guessColorFromLAB(img)
    if labGuess in ["brown", "white", "gray", "black"]:
        return [labGuess]
    return hueGuess

def testSingleColor():
    colorAccuracies = {}
    for color in colors.keys():
        accuracy = [0, 0]
        for filePath in os.listdir("images/%s color" % (color)):
            img = cv2.imread("images/%s color/%s" % (color, filePath))
            try:
                if guessColor(img)[0] == color:
                    accuracy[0] += 1
                accuracy[1] += 1
            except:
                pass
        colorAccuracies[color] = accuracy[0]/accuracy[1]
    return colorAccuracies

def testDoubleColor():
    colorList = list(colors.keys() - ["brown", "white", "gray", "black"])
    colorAccuracies = {}
    for colorTuple in [(c1, c2) for i,c1 in enumerate(colorList) for c2 in colorList[i:] if c1 != c2]:
        accuracy = [0, 0, 0] #2 right, 1 right, total
        extraneous = [0 for i in range(len(colorList))] # how many extra guesses
        count1 = 0
        for color1Path in os.listdir("images/%s color" % (colorTuple[0])):
            count2 = 0
            img1 = cv2.imread("images/%s color/%s" % (colorTuple[0], color1Path))
            for color2Path in os.listdir("images/%s color" % (colorTuple[1])):
                try:
                    img2 = cv2.imread("images/%s color/%s" % (colorTuple[1], color2Path))
                    h = min(img1.shape[0], img2.shape[0])
                    w = min(img1.shape[1], img2.shape[1])
                    img1 = img1[0:h, 0:w]
                    img2 = img2[0:h, 0:w]
                    combinedImg = numpy.concatenate((img1, img2), axis = 1)
                    guess = guessColor(combinedImg)
                    if (colorTuple[0] in guess and colorTuple[1] in guess):
                        accuracy[0] += 1
                        extraneous[len(guess)-2] += 1 # fix this u potato
                    elif (colorTuple[0] in guess or colorTuple[1] in guess):
                        accuracy[1] += 1
                        extraneous[len(guess)-1] += 1
                    accuracy[2] += 1
                    count2 += 1
                    if (count2 > 10):
                        break
                except:
                    pass
            count1 += 1
            if (count1 > 10):
                break
        colorAccuracies[colorTuple] = [accuracy, extraneous]
    return colorAccuracies

#singleColorAccuracies = testSingleColor()
#for k in singleColorAccuracies.keys():
#    print(k, singleColorAccuracies[k])
doubleColorAccuracies = testDoubleColor()
print(doubleColorAccuracies)
for k in doubleColorAccuracies.keys():
    print(" ".join(k), " ".join(map(str, doubleColorAccuracies[k][0] + doubleColorAccuracies[k][1])))