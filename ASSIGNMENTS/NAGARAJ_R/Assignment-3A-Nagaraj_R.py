#Author - Nagaraj_R
from gpiozero import LED
from time import sleep

red = LED(22)
amber = LED(27)
green = LED(17)
while true:
  red.on()
  sleep(1)
  amber.on()
  sleep(1)
  green.on()
  sleep(1)
  red.off()
  sleep(1)
  amber.off()
  sleep(1)
  green.off()