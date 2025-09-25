#!/usr/bin/env python3
"""
VL6180センサーの詳細診断スクリプト
"""
import smbus2
import time
from logging import getLogger, basicConfig, INFO

logger = getLogger(__name__)
basicConfig(level=INFO)

# VL6180のデフォルトアドレス
VL6180_ADDRESS = 0x29

def scan_all_i2c_addresses():
    """全I2Cアドレスをスキャンして検出されたデバイスを表示"""
    logger.info("=== I2Cデバイス全体スキャン ===")
    
    try:
        bus = smbus2.SMBus(1)
        found_devices = []
        
        for addr in range(0x03, 0x78):  # 有効なI2Cアドレス範囲
            try:
                bus.read_byte(addr)
                found_devices.append(addr)
                logger.info(f"✓ デバイス発見: 0x{addr:02X}")
            except:
                pass
        
        if found_devices:
            logger.info(f"発見されたデバイス: {[hex(addr) for addr in found_devices]}")
            if VL6180_ADDRESS in found_devices:
                logger.info("🎯 VL6180センサー (0x29) が発見されました！")
                return True
            else:
                logger.warning("VL6180センサー (0x29) は発見されませんでした")
                return False
        else:
            logger.warning("I2Cデバイスが発見されませんでした")
            return False
            
    except Exception as e:
        logger.error(f"I2Cスキャンエラー: {e}")
        return False
    finally:
        try:
            bus.close()
        except:
            pass

def test_vl6180_basic_communication():
    """VL6180との基本通信をテスト"""
    logger.info("=== VL6180基本通信テスト ===")
    
    try:
        bus = smbus2.SMBus(1)
        
        # VL6180の基本的なレジスタ読み書きテスト
        test_cases = [
            ("システムリセット確認", 0x0016),
            ("モデルID読み取り", 0x0000),
            ("リビジョンID読み取り", 0x0001),
            ("モジュールID読み取り", 0x0002),
        ]
        
        success_count = 0
        
        for description, reg_addr in test_cases:
            try:
                logger.info(f"テスト中: {description} @ 0x{reg_addr:04X}")
                
                # VL6180は16bitアドレスなので分割
                a1 = (reg_addr >> 8) & 0xFF
                a0 = reg_addr & 0xFF
                
                bus.write_i2c_block_data(VL6180_ADDRESS, a1, [a0])
                time.sleep(0.01)
                
                result = bus.read_byte(VL6180_ADDRESS)
                logger.info(f"✓ {description} 成功: 0x{result:02X}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"✗ {description} 失敗: {e}")
        
        logger.info(f"通信テスト結果: {success_count}/{len(test_cases)} 成功")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"VL6180通信テスト中のエラー: {e}")
        return False
    finally:
        try:
            bus.close()
        except:
            pass

def check_vl6180_power_and_wiring():
    """VL6180の電源と配線をチェック"""
    logger.info("=== VL6180電源・配線チェック ===")
    
    logger.info("確認項目:")
    logger.info("1. 電源電圧: VL6180は2.8V〜3.6V (3.3V推奨)")
    logger.info("2. SDA接続: GPIO 2 (ピン3)")
    logger.info("3. SCL接続: GPIO 3 (ピン5)")
    logger.info("4. VDD接続: 3.3V (ピン1)")
    logger.info("5. GND接続: GND (ピン6)")
    logger.info("6. プルアップ抵抗: SDA/SCLに4.7kΩ〜10kΩ")
    
    # 簡単な電気的チェック
    try:
        import subprocess
        result = subprocess.run(['gpio', 'readall'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("GPIO状態:")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'SDA' in line or 'SCL' in line:
                    logger.info(f"  {line}")
    except:
        logger.warning("GPIO状態の確認に失敗")

def diagnose_vl6180_issues():
    """VL6180の問題を総合診断"""
    logger.info("=== VL6180センサー総合診断 ===")
    
    issues_found = []
    
    # 1. I2Cデバイススキャン
    logger.info("\n1. I2Cデバイススキャン")
    if not scan_all_i2c_addresses():
        issues_found.append("VL6180センサーがI2Cで検出されない")
    
    # 2. 基本通信テスト
    logger.info("\n2. VL6180基本通信テスト")
    if not test_vl6180_basic_communication():
        issues_found.append("VL6180との基本通信が失敗")
    
    # 3. 電源・配線チェック
    logger.info("\n3. 電源・配線チェック")
    check_vl6180_power_and_wiring()
    
    # 結果とアドバイス
    logger.info("\n=== 診断結果とアドバイス ===")
    
    if issues_found:
        logger.error("発見された問題:")
        for issue in issues_found:
            logger.error(f"  - {issue}")
        
        logger.info("\n💡 VL6180センサーのトラブルシューティング:")
        logger.info("1. 配線確認:")
        logger.info("   - VDD → 3.3V (ピン1)")
        logger.info("   - GND → GND (ピン6)")  
        logger.info("   - SDA → GPIO 2 (ピン3)")
        logger.info("   - SCL → GPIO 3 (ピン5)")
        
        logger.info("2. 電源確認:")
        logger.info("   - VL6180は3.3V専用（5Vは使用不可）")
        logger.info("   - 電流供給が十分か確認")
        
        logger.info("3. センサー確認:")
        logger.info("   - VL6180センサーモジュールが正常か確認")
        logger.info("   - 他のI2Cアドレス（0x52など）を試す")
        
        logger.info("4. プルアップ抵抗:")
        logger.info("   - SDA/SCLに4.7kΩ〜10kΩのプルアップ抵抗が必要")
        logger.info("   - 一部のモジュールには内蔵されている")
        
    else:
        logger.info("✅ 大きな問題は検出されませんでした")
        logger.info("センサーは正常に動作するはずです")

if __name__ == "__main__":
    diagnose_vl6180_issues()