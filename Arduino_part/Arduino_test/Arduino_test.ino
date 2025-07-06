void setup() {
  Serial.begin(9600);  // 打开串口监视器
  delay(1000);
  Serial.println("准备开始读取 Velostat 输入值...");
}

void loop() {
  int val = analogRead(A0);  // 读取 A0 引脚的模拟值（0~1023）
  
  // 打印模拟值和对应电压（可选）
  Serial.print("analogRead(A0): ");
  Serial.print(val);
  Serial.print("   voltage: ");
  Serial.print((val * 5.0) / 1023.0, 2);  // 估算电压值
  Serial.println(" V");

  delay(500);  // 每 100 毫秒读取一次
}
