#!/usr/bin/env python3
"""
SHT31センサーの詳細診断スクリプト - 拡張ボード対応版
"""
import smbus2
import time
from logging import getLogger, basicConfig, INFO

logger = getLogger(__name__)
basicConfig(level=INFO)

# SHT31のデフォルトアドレス
SHT31_ADDRESS = 0x44

def test_i2c_read_byte(bus, address):
    """基本的なI2C読み取りテスト"""
    try:
        result = bus.read_byte(address)
        logger.info(f"✓ read_byte成功: 0x{result:02X}")
        return True
    except Exception as e:
        logger.error(f"✗ read_byte失敗: {e}")
        return False

def test_i2c_write_read_cycle(bus, address):
    """書き込み→読み取りサイクルのテスト"""
    try:
        # SHT31の温度・湿度測定コマンド（低速、高信頼性）
        logger.info("SHT31測定コマンド（低速モード）を送信中...")
        bus.write_i2c_block_data(address, 0x2C, [0x10])  # 低速、高信頼性モード
        time.sleep(1.0)  # 測定完了まで待機
        
        # データ読み取り
        logger.info("測定データを読み取り中...")
        data = bus.read_i2c_block_data(address, 0x00, 6)
        logger.info(f"✓ データ読み取り成功: {[hex(x) for x in data]}")
        
        # 温度・湿度を計算
        temp_raw = (data[0] << 8) | data[1]
        hum_raw = (data[3] << 8) | data[4]
        
        temperature = -45 + (175 * temp_raw / 65535.0)
        humidity = 100 * hum_raw / 65535.0
        
        logger.info(f"🌡️  温度: {temperature:.2f}°C")
        logger.info(f"💧 湿度: {humidity:.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 書き込み→読み取りサイクル失敗: {e}")
        return False

def test_different_commands(bus, address):
    """異なるSHT31コマンドをテスト"""
    commands = [
        (0x30, [0xA2], "ソフトリセット"),
        (0xF3, [0x2D], "ステータス読み取り"),
        (0x2C, [0x06], "高速測定"),
        (0x2C, [0x10], "中速測定"),
        (0x2C, [0x16], "低速測定"),
    ]
    
    success_count = 0
    
    for reg, data, description in commands:
        try:
            logger.info(f"テスト中: {description}")
            bus.write_i2c_block_data(address, reg, data)
            time.sleep(0.1)
            logger.info(f"✓ {description} - コマンド送信成功")
            success_count += 1
        except Exception as e:
            logger.error(f"✗ {description} - 失敗: {e}")
    
    logger.info(f"コマンドテスト結果: {success_count}/{len(commands)} 成功")
    return success_count > 0

def test_clock_stretching_tolerance():
    """クロックストレッチング耐性をテスト"""
    logger.info("I2Cクロックストレッチング設定を確認中...")
    
    try:
        # I2Cバスの設定を確認
        import subprocess
        result = subprocess.run(['i2cget', '-y', '1', '0x44'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            logger.info("✓ i2cget での基本通信成功")
            return True
        else:
            logger.error(f"✗ i2cget 失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ i2cget タイムアウト - クロックストレッチングの問題の可能性")
        return False
    except Exception as e:
        logger.error(f"✗ i2cget テストエラー: {e}")
        return False

def diagnose_expansion_board_issues():
    """拡張ボード特有の問題を診断"""
    logger.info("=== 拡張ボード問題診断 ===")
    
    issues_found = []
    
    try:
        bus = smbus2.SMBus(1)
        
        # 1. 基本的な通信テスト
        logger.info("1. 基本I2C通信テスト")
        if not test_i2c_read_byte(bus, SHT31_ADDRESS):
            issues_found.append("基本I2C通信失敗")
        
        # 2. クロックストレッチングテスト
        logger.info("\n2. クロックストレッチングテスト")
        if not test_clock_stretching_tolerance():
            issues_found.append("クロックストレッチング問題")
        
        # 3. 異なるコマンドテスト
        logger.info("\n3. SHT31コマンドテスト")
        if not test_different_commands(bus, SHT31_ADDRESS):
            issues_found.append("SHT31コマンド実行失敗")
        
        # 4. 完全な測定サイクルテスト
        logger.info("\n4. 完全測定サイクルテスト")
        if not test_i2c_write_read_cycle(bus, SHT31_ADDRESS):
            issues_found.append("完全測定サイクル失敗")
            
    except Exception as e:
        logger.error(f"診断中にエラー: {e}")
        issues_found.append(f"診断エラー: {e}")
    finally:
        try:
            bus.close()
        except:
            pass
    
    # 結果報告
    logger.info("\n=== 診断結果 ===")
    if issues_found:
        logger.error("発見された問題:")
        for issue in issues_found:
            logger.error(f"  - {issue}")
        
        logger.info("\n💡 拡張ボード使用時の解決方法:")
        logger.info("1. I2Cプルアップ抵抗の確認（通常4.7kΩ）")
        logger.info("2. I2Cクロック速度の低下")
        logger.info("3. 電源電圧の安定性確認（3.3V）")
        logger.info("4. 配線の接触確認")
        logger.info("5. 拡張ボードのI2C信号品質確認")
        
    else:
        logger.info("✅ 大きな問題は検出されませんでした")

if __name__ == "__main__":
    diagnose_expansion_board_issues()