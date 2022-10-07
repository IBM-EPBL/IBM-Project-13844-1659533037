//https://www.tinkercad.com/things/i6nog5uGY0N - Link For The TinkerCAD Project Smart Home 
//Assignment - 01 
//Author :- Dheeraj Prakash . S (Team Leader)
#include<Servo.h>

#define myLed 8

Servo s;

void setup()
{
  Serial.begin(9600);
  pinMode(4, INPUT);
  pinMode(myLed, OUTPUT);
  s.attach(7);
  pinMode(2, OUTPUT);
}

void loop()
{
  int p = digitalRead(4);
  Serial.println(p);
  
  if(p){
    Serial.println("Welcome Home!! The doors will open soon");
    
    digitalWrite(myLed, HIGH);
    
    tone(2, 30000);
    delay(500);
    noTone(2);
    
    for(int i = 0; i <=180; i++){
    	s.write(i);
    	delay(10);
  	}
  	delay(1000);
  	for(int j = 180; j >=0; j--){
    	s.write(j);
    	delay(10);
  	}
    
  }
}
