import smbus2
from typing import Tuple, List, Sequence
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

ADDRESS = 0x44

COMMAND_MEAS_CLKST = 0x2C
COMMAND_MEAS_HIGHREP = [0x06]


class SHT31(object):
    def __init__(self, address: int = ADDRESS, test_mode: bool = False) -> None:
        """Temperature and Humidity Sensor Client Object.
        See: https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf

        Args:
            address: Temperature and Humidity Sensor address
            test_mode: If True, returns mock data instead of reading from sensor
        """
        self._address = address
        self._test_mode = test_mode
        if not test_mode:
            self._bus = smbus2.SMBus(1)
            logger.info("SHT31 sensor is starting...")
        else:
            self._bus = None
            logger.info("SHT31 sensor is starting in TEST MODE...")

    def get_temperature(self) -> float:
        """Read the temperature from the sensor and return it.

        Returns:
            temperature value
        """
        temperature, humidity = self.get_temperature_humidity()
        return temperature

    def get_humidity(self) -> float:
        """Read the humidity from the sensor and return it.

        Returns:
            humidity value
        """
        temperature, humidity = self.get_temperature_humidity()
        return humidity

    def get_temperature_humidity(self) -> Tuple[float, float]: #温度,湿度を返す
        """Read the temperature, humidity from the sensor and return it. 

        Returns:
            temperature, humidity value
        """
        if self._test_mode:
            # テストモード: モックされた値を返す
            import random
            temperature = 20.0 + random.uniform(-5, 15)  # 15-35°C
            humidity = 50.0 + random.uniform(-20, 30)    # 30-80%
            return temperature, humidity
            
        try:
            self.write_list(COMMAND_MEAS_CLKST, COMMAND_MEAS_HIGHREP) #測定を指示
            sleep(0.5)

            data = self.read_list(0x00, 6) #測定結果の読み取りを指示
            temperature = -45 + (175 * (data[0] * 256 + data[1]) / 65535.0) #温度計算式
            humidity = 100 * (data[3] * 256 + data[4]) / 65535.0 #湿度計算式

            return temperature, humidity #温度,湿度を返す
        except (TimeoutError, OSError) as e:
            logger.error(f"SHT31センサーとの通信エラー: {e}")
            logger.error("センサーが接続されていない可能性があります。--testオプションを使用してテストモードで実行してください。")
            raise

    def read(self, register: int) -> int:
        """Read and return a byte from the specified 16-bit register address.

        Args:
            register: sensor register address

        Returns:
            Temperature and Humidity Sensor data
        """
        if self._test_mode:
            return 0xFF  # テストモード用のダミーデータ
        return self._bus.read_byte_data(self._address, register) & 0xFF

    def read_list(self, register: int, length: int) -> List:
        """Read and return a byte list from the specified 16-bit register address.

        Args:
            register: sensor register address
            length: read byte length

        Returns:
            Temperature and Humidity Sensor data
        """
        if self._test_mode:
            # SHT31の温度・湿度データ用のダミーデータ
            return [0x67, 0x89, 0xAB, 0x80, 0x12, 0xCD]  # テストモード用のダミーデータ
        return self._bus.read_i2c_block_data(self._address, register, length)

    def write(self, register: int, value: int) -> None:
        """Write 1 byte of data from the specified 16-bit register address.

        Args:
            register: sensor register address
            value: write data
        """
        if self._test_mode:
            return  # テストモードでは何もしない
        value = value & 0xFF
        self._bus.write_byte_data(self._address, register, value)

    def write_list(self, register: int, data: Sequence[int]) -> None:
        """Write 1 byte of data from the specified 16-bit register address.

        Args:
            register: sensor register address
            data: write data
        """
        if self._test_mode:
            return  # テストモードでは何もしない
        self._bus.write_i2c_block_data(self._address, register, data)


def debug() -> None:
    """debug function.
    """
    import argparse #実行時の測定間隔を指定するために使用
    parser = argparse.ArgumentParser(
        description="Temperature and Humidity Sensor Script"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds" #デフォルトは10秒,-iに続けて数値を指定することで変更可能
    )
    parser.add_argument(
        "-t", "--test", action="store_true", help="run in test mode (no sensor required)"
    )
    args = parser.parse_args()

    sensor = SHT31(test_mode=args.test)
    try:
        while True: #取得した温度、湿度を指定した間隔でログに出力し続ける
            temperature, humidity = sensor.get_temperature_humidity()
            logger.info("Temperature: {} C, Humidity: {} %".format(temperature, humidity))
            sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("プログラムが中断されました。")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        logger.info("解決方法:")
        logger.info("1. SHT31センサーが正しく接続されているか確認してください")
        logger.info("2. I2Cが有効になっているか確認してください")
        logger.info("3. センサーなしでテストする場合は --test オプションを使用してください")
        logger.info("   例: python3 SHT31.py --test --interval 5")


if __name__ == "__main__":
    debug()
