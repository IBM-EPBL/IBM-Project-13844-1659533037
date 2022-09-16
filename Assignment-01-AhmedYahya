//Author Ahmed Yahya
//Assignment - 01

#define R 10
#define G 8
#define B 9

int sensor=6;
int val=0;
void setup()
{
  pinMode(6,INPUT);
  pinMode(R, OUTPUT);
  pinMode(G, OUTPUT);
  pinMode(B, OUTPUT);
  pinMode(11,OUTPUT);
  Serial.begin(9600);
}

void loop()
{
  val=digitalRead(sensor);
  if(val==HIGH)
  {
    analogWrite(R, random(255));
    analogWrite(G, random(255));
    analogWrite(B, random(255));
    tone(11,50);
    delay(200);
  }    
  else
  {
    noTone(11);
    delay(1000);
  }
}
