import pymem
import pymem.ressources.structure
import pymem.process
import pymem.pattern
import pymem.memory
import pymem.exception
import keyboard
import time
import slider
import ctypes 
import os
import sys
import interception
from tkinter.filedialog import askopenfilename

os.system("title Clarity Overlay")

#Initializing variables
user32 = ctypes.windll.user32
processFound = False
started = False
mouse_movements = False
key_presses = False
LOADED = False
flip = False
rp = []
coords = ()
c = 0
sx = 0
sy = 0
file_path = None


# osu! signatures (https://github.com/l3lackShark/gosumemory/blob/master/memory/read.go)
timeSignature = rb"\x5E\x5F\x5D\xC3\xA1....\x89.\x04"
statusSignature = rb"\x48\x83\xF8\x04\x73\x1E"
timeAddr = None
statusAddr = None
replayPath = None


oneTimeK1 = True
oneTimeK2 = True

# Opening handle to the game
        
while processFound != True:
    try:
        pId = pymem.process.process_from_name("osu!.exe").th32ProcessID
        if pId:
            pHandle = pymem.process.open(pId, False, 
                                pymem.ressources.structure.PROCESS.PROCESS_QUERY_INFORMATION | 
                                pymem.ressources.structure.PROCESS.PROCESS_VM_READ)
            processFound = True
    except pymem.exception.ProcessNotFound:
        pass
    except pymem.exception.WinAPIError:
        pass


# Resolving addresses 
timePattern = pymem.pattern.pattern_scan_all(pHandle, timeSignature, return_multiple=False)
timeAddr = pymem.memory.read_int(pHandle, timePattern + 0x5)
statusPattern = pymem.pattern.pattern_scan_all(pHandle, statusSignature, return_multiple=False)
statusAddr = pymem.memory.read_uint(pHandle, statusPattern - 0x4)

def bannerprint(m_m, k_p, f, f_p):
    banner = (f"""
Replay bot
(M) Mouse movements : {m_m}
(K) Key presses : {k_p}
(F) Flip Replay (HR) : {f}
(ESC) Stop the bot
(ENTER) Start the bot
(F4) Leave
Replay loaded : {f_p}

""")
    print(banner)

def main():

    global c, sx, sy, rp, started, mouse_movements, key_presses, LOADED, flip, file_path, processFound, coords, replayPath, oneTimeK1, oneTimeK2
    
    
    # Scaling 
    c = (4 / 3) / (user32.GetSystemMetrics(0) / user32.GetSystemMetrics(1))
    sx = user32.GetSystemMetrics(0) / 2 - (0.8 * user32.GetSystemMetrics(0) * c) / 2
    sy = 0.2 * user32.GetSystemMetrics(1) * (11 / 19)

    os.system("cls")
    
    bannerprint(mouse_movements, key_presses, flip, file_path)

    while not keyboard.is_pressed("F4"):
        try:

            curr_status = pymem.memory.read_uint(pHandle, statusAddr)

            if keyboard.is_pressed("l"):
                LOADED = False
                try:
                    # Search for a replay
                    replayPath = askopenfilename(filetypes=[(".osr files", "*.osr")])
                    replayPath = replayPath.replace("/", "\\")
                    replay = slider.Replay.from_path(replayPath, retrieve_beatmap=False)
                    rp = replay.actions
                    os.system("cls")
                    bannerprint(mouse_movements, key_presses, flip, replayPath)
                    time.sleep(0.15)
                except FileNotFoundError:
                    print("[*] Replay not found, please retry.") 
                    time.sleep(3)
                    os.system("cls")
                    bannerprint(mouse_movements, key_presses, flip, replayPath)
                    continue
                else:
                    LOADED = True

            # Enable / Disable mouse movements
            elif keyboard.is_pressed("m"):
                mouse_movements = not mouse_movements
                os.system("cls")
                bannerprint(mouse_movements, key_presses, flip, replayPath)
                time.sleep(0.15)

            # Enable / Disable key presses
            elif keyboard.is_pressed("k"):
                key_presses = not key_presses
                os.system("cls")
                bannerprint(mouse_movements, key_presses, flip, replayPath)
                time.sleep(0.15)

            # Enable / Disable flipping replay (HR)
            elif keyboard.is_pressed("f"):
                flip = not flip
                os.system("cls")
                bannerprint(mouse_movements, key_presses, flip, replayPath)
                time.sleep(0.15)
            

            #start playing
            elif keyboard.is_pressed("enter") and curr_status == 2:
                ind = 1

                while len(rp) - 2 > ind and not keyboard.is_pressed("esc") and LOADED:
                    curr_time = pymem.memory.read_int(pHandle, timeAddr)

                    if curr_time <= int((rp[ind].offset.seconds + rp[ind].offset.microseconds/1000000)*1000) and not started:
                        if not int((rp[ind].offset.seconds + rp[ind].offset.microseconds/1000000)*1000) >= 86300000:
                            started = True
                        ind += 1
                    
                    else:
                        if curr_time >= int((rp[ind].offset.seconds + rp[ind].offset.microseconds/1000000)*1000):
                            # Convert the coordinates 
                            xCoords = int((sx + rp[ind].position.x * user32.GetSystemMetrics(0) * 0.8 * c / 512))
                            yCoords = int((sy + rp[ind].position.y * user32.GetSystemMetrics(1) * 0.8 / 384))
                            yFlippedCoords = int((sy + (384 - rp[ind].position.y) * user32.GetSystemMetrics(1) * 0.8 / 384))


                            # Move mouse
                            if mouse_movements:
                                # If flip mode is enabled then move the mouse like a HR replay
                                if flip:
                                    interception.move_to(xCoords,  yFlippedCoords)
                                else:
                                    
                                    interception.move_to(xCoords,  yCoords)
                            
                            if key_presses:
                                if rp[ind].key1 == True:
                                    if oneTimeK1:
                                        interception.key_down("w")
                                        oneTimeK1 = False
                                    
                                if rp[ind].key1 == False or keyboard.is_pressed("esc"):
                                    if not oneTimeK1:
                                        interception.key_up("w")
                                        oneTimeK1 = True


                                if rp[ind].key2 == True:
                                    if oneTimeK2:
                                        interception.key_down("x")
                                        oneTimeK2 = False
                                if rp[ind].key2 == False or keyboard.is_pressed("esc"):
                                    if not oneTimeK2:
                                        interception.key_up("x")
                                        oneTimeK2 = True
                                
                                
                            ind += 1

                # Reset the variables
                interception.key_up("w")
                interception.key_up("x")
                ind = 1
                started = False

        except pymem.exception.MemoryReadError:
            os.system("cls")
            print("\33[38;5;196m[*] ERROR : Couldn't read memory. Please verify that osu! is correctly opened. Leaving in 3 seconds.")
            time.sleep(3)
            sys.exit()
            
            
if __name__ == "__main__":
    main()
