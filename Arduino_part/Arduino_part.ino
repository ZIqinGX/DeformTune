void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("Arduino 准备就绪...");
}

void loop() {
  int rawA0 = analogRead(A0);  // 读取 A0
  int rawA1 = analogRead(A1);  // 读取 A1

  // 映射为 -1.0 ~ 0.0（Arduino 模拟输入为 0~1023）
  float a0 = -1.0 + (float(rawA0) / 1023.0);
  float a1 = -1.0 + (float(rawA1) / 1023.0);

  // 打印格式为: -0.582,-0.293
  Serial.print(a0, 4);
  Serial.print(",");
  Serial.println(a1, 4);

  delay(1000);  // 每 100ms 发送一次
}
