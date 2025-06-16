import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import time
import random
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
detector = HandDetector(detectionCon=0.8, maxHands=1)
# Game variables
playerName = ""
cursorVisible = True
lastCursorToggle = time.time()
invalidInput = False
invalidTimer = 0
aiName = ""
scoreLimit = 0
finalText = ""
nameStage = 0  # 0 = Score Limit, 1 = AI Name, 2 = Player Name
keyboardVisible = True
startGame = False
stateResult = False
scores = [0, 0]
initialTime = 0
timer = 0
gameInProgress = False
waitForNextRound = True
aiMove = None
aiImage = None
roundCompleted = False  # Prevents continuous moves until 'S' is pressed again
winnerDeclared = False  # To show winner message once and quit after
# Keyboard layouts
alphaKeys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
             ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
             ["Z", "X", "C", "V", "B", "N", "M", "<", "SPACE", "ENTER"]]
numKeys = [["7", "8", "9"],
           ["4", "5", "6"],
           ["1", "2", "3"],["0", "<", "ENTER"]]
currentKeys = numKeys  # Start with number keys for score limit
def createKeyList(keys):
    keyList = []
    for i in range(len(keys)):
        row = keys[i]
        x_offset = 50
        for key in row:
            if key == "SPACE":
                w = 170  # Wider for SPACE
            elif key == "ENTER":
                w = 130  # Wider for ENTER
            else:
                w = 85
            keyList.append({'pos': (x_offset, 100 * i + 50), 'text': key, 'size': (w, 85)})
            x_offset += w + 15  # Add gap between keys
    return keyList
keyList = createKeyList(currentKeys)
def drawKeyboard(img):
    for key in keyList:
        x, y = key['pos']
        w, h = key['size']
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), cv2.FILLED)
        text_offset_x = 20 if key['text'] not in ["SPACE", "ENTER"] else 10
        cv2.putText(img, key['text'], (x + text_offset_x, y + 55),
                    cv2.FONT_HERSHEY_PLAIN, 2.5, (255, 255, 255), 3)
    return img
def checkKeyPress(fingerPos):
    for key in keyList:
        x, y = key['pos']
        w, h = key['size']
        if x < fingerPos[0] < x + w and y < fingerPos[1] < y + h:
            return key['text']
    return None
def drawPurpleButton(img):
    x, y, w, h = 1100, 50, 150, 80
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), cv2.FILLED)
    cv2.putText(img, "KB", (x + 10, y + 55), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
    return (x, y, w, h)
def isInButton(pos, buttonRect):
    x, y, w, h = buttonRect
    return x < pos[0] < x + w and y < pos[1] < y + h
while True:
    success, img = cap.read()
    #img = cv2.flip(img, 1)
    imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875)
    imgScaled = imgScaled[:, 80:480]
    hands, img = detector.findHands(img)
    # Update keyboard layout based on stage
    if keyboardVisible:
        if nameStage == 0:
            if currentKeys != numKeys:
                currentKeys = numKeys
                keyList = createKeyList(currentKeys)
        else:
            if currentKeys != alphaKeys:
                currentKeys = alphaKeys
                keyList = createKeyList(currentKeys)
        img = drawKeyboard(img)
        if hands:
            lmList = hands[0]["lmList"]
            indexFinger = lmList[8]
            middleFinger = lmList[12]
            keyPressed = None
            for key in keyList:
                x, y = key['pos']
                w, h = key['size']  # ✅ Use actual key size
                if x < indexFinger[0] < x + w and y < indexFinger[1] < y + h:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                    text_offset_x = 20 if key['text'] not in ["SPACE", "ENTER"] else 10
                    cv2.putText(img, key['text'], (x + text_offset_x, y + 55),
                                cv2.FONT_HERSHEY_PLAIN, 2.5, (255, 255, 255), 3)
                    if abs(indexFinger[1] - middleFinger[1]) < 30:
                        keyPressed = key['text']
                        time.sleep(0.4)
                        break
            if keyPressed is not None:
                if keyPressed == "<":
                    finalText = finalText[:-1]
                elif keyPressed == "SPACE":
                    finalText += " "
                elif keyPressed == "ENTER":
                    if nameStage == 0:
                        if finalText.isdigit() and int(finalText) > 0:
                            scoreLimit = int(finalText)
                            finalText = ""
                            nameStage = 1
                            invalidInput = False
                        else:
                            invalidInput = True
                            invalidTimer = time.time()
                    elif nameStage == 1:
                        if finalText.strip():
                            aiName = finalText.strip()
                            finalText = ""
                            nameStage = 2
                            invalidInput = False
                        else:
                            invalidInput = True
                            invalidTimer = time.time()
                    elif nameStage == 2:
                        if finalText.strip():
                            if finalText.strip().lower() == aiName.strip().lower():
                                invalidInput = True
                                invalidTimer = time.time()
                                finalText = ""  # Optional: clear input so user retypes
                            else:
                                playerName = finalText.strip()
                                finalText = ""
                                nameStage = 3
                                keyboardVisible = False
                                invalidInput = False
                        else:
                            invalidInput = True
                            invalidTimer = time.time()
                else:
                    if nameStage == 0:
                        if keyPressed.isdigit():
                            finalText += keyPressed
                    else:
                        finalText += keyPressed
    else:
        if not keyboardVisible:
            buttonRect = drawPurpleButton(img)
            if hands:
                lmList = hands[0]["lmList"]
                indexFinger = lmList[8]
                middleFinger = lmList[12]
                if isInButton(indexFinger, buttonRect):
                    if abs(indexFinger[1] - middleFinger[1]) < 30:
                        # ✅ Draw pressed button in green
                        x, y, w, h = buttonRect
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, "KB", (x + 10, y + 55), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                        keyboardVisible = True
                        time.sleep(0.5)
    if nameStage == 0:
        promptText = "Enter SCORE LIMIT and press ENTER"
        displayText = finalText
    elif nameStage == 1:
        promptText = "Enter AI NAME and press ENTER"
        displayText = finalText
    elif nameStage == 2:
        promptText = "Enter YOUR NAME and press ENTER"
        displayText = finalText
    else:
        promptText = "Press 'S' to start the game, 'R' to restart and 'Q' to quit the game"
        displayText = f"{playerName} VS {aiName} | Score to win: {scoreLimit}"
    if invalidInput and time.time() - invalidTimer < 2:
        if nameStage == 2 and finalText == "":
            cv2.putText(img, "AI and Player name cannot be the same!", (300, 400), cv2.FONT_HERSHEY_PLAIN, 2.5,
                        (0, 0, 0), 3)
        else:
            cv2.putText(img, "Enter valid input!", (500, 100), cv2.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 0), 3)
    cv2.putText(img, promptText, (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
    cv2.rectangle(img, (40, 440), (1240, 500), (0, 0, 0), cv2.FILLED)
    # Blinking cursor logic
    if time.time() - lastCursorToggle > 0.5:
        cursorVisible = not cursorVisible
        lastCursorToggle = time.time()
    # Append cursor if visible
    displayTextWithCursor = displayText + "|" if cursorVisible else displayText
    cv2.putText(img, displayTextWithCursor, (60, 490), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
    if startGame:
        cv2.putText(img, f"{playerName}: {scores[0]}", (50, 650), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
        cv2.putText(img, f"{aiName}: {scores[1]}", (800, 650), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
    if startGame:
        if not stateResult:
            timer = time.time() - initialTime
            cv2.putText(img, f"Timer: {int(timer)}", (500, 650), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 255), 3)
            if timer > 3:
                stateResult = True
                roundCompleted = True  # Mark round as done
                playerMove = None
                if hands:
                    hand = hands[0]
                    fingers = detector.fingersUp(hand)
                    if fingers == [0, 0, 0, 0, 0]:
                        playerMove = 1  # Rock
                    elif fingers == [1, 1, 1, 1, 1]:
                        playerMove = 2  # Paper
                    elif fingers == [0, 1, 1, 0, 0]:
                        playerMove = 3  # Scissors
                aiMove = random.randint(1, 3)
                aiImage = cv2.imread(f'Resources/{aiMove}.png', cv2.IMREAD_UNCHANGED)
                # Only show AI move on left side if it's not the final winning round
                if not ((scores[0] + 1 >= int(scoreLimit)) or (scores[1] + 1 >= int(scoreLimit))):
                    img = cvzone.overlayPNG(img, aiImage, (220, 200))
                if playerMove is None:
                    scores[1] += 1  # No hand detected, AI gets the point
                else:
                    if (playerMove == 1 and aiMove == 3) or (playerMove == 2 and aiMove == 1) or (
                            playerMove == 3 and aiMove == 2):
                        scores[0] += 1
                    elif (aiMove == 1 and playerMove == 3) or (aiMove == 2 and playerMove == 1) or (
                            aiMove == 3 and playerMove == 2):
                        scores[1] += 1
                if scores[0] >= int(scoreLimit):
                    winnerDeclared = True
                    winnerName = playerName
                elif scores[1] >= int(scoreLimit):
                    winnerDeclared = True
                    winnerName = aiName
        else:

            if 'aiImage' in locals():
                img = cvzone.overlayPNG(img, aiImage, (990,400))  # Match new position
    if not keyboardVisible and not startGame:
        cv2.putText(img, "Press Purple KEYBOARD button to open virtual keyboard", (50, 690), cv2.FONT_HERSHEY_PLAIN, 2, (200, 0, 200), 2)
    if not keyboardVisible and startGame:
        cv2.putText(img, "Game running - Press virtual 'R' to restart, 'Q' to quit", (50, 690), cv2.FONT_HERSHEY_PLAIN, 2, (200, 0, 200), 2)
    if keyboardVisible and nameStage > 2:
        if hands:
            lmList = hands[0]["lmList"]
            indexFinger = lmList[8]
            middleFinger = lmList[12]
            keyPressed = None
            for key in keyList:
                x, y = key['pos']
                w, h = key['size']  # ✅ Use actual key size
                if x < indexFinger[0] < x + w and y < indexFinger[1] < y + h:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                    text_offset_x = 20 if key['text'] not in ["SPACE", "ENTER"] else 10
                    cv2.putText(img, key['text'], (x + text_offset_x, y + 55),
                                cv2.FONT_HERSHEY_PLAIN, 2.5, (255, 255, 255), 3)
                    if abs(indexFinger[1] - middleFinger[1]) < 30:
                        keyPressed = key['text']
                        time.sleep(0.4)
                        break
            if keyPressed is not None:
                if keyPressed.lower() == 's':
                    if not startGame:
                        startGame = True
                        roundCompleted = False
                        stateResult = False
                        initialTime = time.time()
                    elif roundCompleted:
                        startGame = True
                        roundCompleted = False
                        stateResult = False
                        initialTime = time.time()
                elif keyPressed.lower() == 'r':
                    startGame = False
                    stateResult = False
                    roundCompleted = False
                    scores = [0, 0]
                    playerName = ""
                    aiName = ""
                    scoreLimit = ""
                    finalText = ""
                    nameStage = 0
                    currentKeys = numKeys
                    keyList = createKeyList(currentKeys)
                    keyboardVisible = True
                elif keyPressed.lower() == 'q':
                    break
    if winnerDeclared:
        if aiImage is not None:
            img = cvzone.overlayPNG(img, aiImage, (950, 400))  # ⬅️ Show AI move at bottom right
        cv2.rectangle(img, (200, 250), (1000, 450), (0, 0, 0), cv2.FILLED)
        cv2.putText(img, f"{winnerName} has won!!", (300, 400),
                    cv2.FONT_HERSHEY_PLAIN, 5, (0, 255, 0), 5)
        cv2.imshow("Rock Paper Scissors Virtual Keyboard", img)
        cv2.waitKey(2000)  # Wait 2 seconds
        break # Exit game
    cv2.imshow("Rock Paper Scissors Virtual Keyboard", img)
    key = cv2.waitKey(1)
    if key == 27:
        break
cap.release()
cv2.destroyAllWindows()
