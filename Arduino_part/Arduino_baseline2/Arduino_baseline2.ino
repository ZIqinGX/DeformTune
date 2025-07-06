// ========= 1. 类的定义部分（封装） =========
class PressureSensor {
  public:
    PressureSensor(int pin, float alpha = 0.1, int minStableFrames = 50, float noiseThreshold = 0.01) {
      _pin = pin;
      _alpha = alpha;
      _minStableFrames = minStableFrames;
      _noiseThreshold = noiseThreshold;
      _minVal = 1.0;
      _maxVal = 0.0;
      _stableCount = 0;
      _smoothed = 0.0;
    }

    void update() {
      float val = analogRead(_pin) / 1023.0;
      _smoothed = _alpha * val + (1 - _alpha) * _smoothed;

      if (abs(_smoothed - _minVal) < _noiseThreshold) {
        _stableCount++;
        if (_stableCount > _minStableFrames) {
          _minVal = (_minVal * 9 + _smoothed) / 10.0;
          _stableCount = _minStableFrames;
        }
      } else {
        _stableCount = 0;
      }

      if (_smoothed > _maxVal) {
        _maxVal = _smoothed;
      }
    }

    int getMappedValue() {
      float norm = (_smoothed - _minVal) / (_maxVal - _minVal + 0.0001);
      norm = constrain(norm, 0.0, 1.0);
      return 1 + int(norm * 9);
    }

    bool isActivated(float threshold = 0.01) {
      return (_smoothed - _minVal) > threshold;
    }

    // ✅ 添加这两个 getter 方法
    float getSmoothed() {
      return _smoothed;
    }

    float getMin() {
      return _minVal;
    }

  private:
    int _pin;
    float _alpha;
    float _smoothed;
    float _minVal;
    float _maxVal;
    int _stableCount;
    int _minStableFrames;
    float _noiseThreshold;
};


// ========= 2. 实例化 & 主程序部分 =========
PressureSensor sensorA0(A0);  // 你可以同时加 sensorA1(A1) 等
PressureSensor sensorA1(A1);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;

void setup() {
  Serial.begin(9600);
  delay(1000);
}
void loop() {
  sensorA0.update();
  sensorA1.update();

  // 当检测到 A0 或 A1 被按压（差值大于一定阈值）时触发
  if (sensorA0.isActivated(0.01) || sensorA1.isActivated(0.01)) {
    unsigned long now = millis();
    if (now - lastSendTime > sendInterval) {
      int val0 = sensorA0.getMappedValue();  // A0 控制值
      int val1 = sensorA1.getMappedValue();  // A1 控制值

      Serial.print(val0);
      Serial.print(",");
      Serial.println(val1);

      lastSendTime = now;
    }
  }
}
