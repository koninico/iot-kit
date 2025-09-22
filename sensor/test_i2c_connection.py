#!/usr/bin/env python3
"""
SHT31センサーとの通信をテストするスクリプト
"""
import smbus2
import time
from logging import getLogger, basicConfig, INFO

logger = getLogger(__name__)
basicConfig(level=INFO)

# SHT31のデフォルトアドレス
SHT31_ADDRESS = 0x44

def test_i2c_connection():
    """I2C接続とSHT31センサーをテストする"""
    logger.info("I2Cバスとの接続をテストしています...")
    
    try:
        # I2Cバスを開く
        bus = smbus2.SMBus(1)
        logger.info("I2Cバス1への接続成功")
        
        # SHT31センサーへの接続をテスト
        logger.info(f"SHT31センサー (アドレス 0x{SHT31_ADDRESS:02X}) との通信をテストしています...")
        
        # SHT31のソフトリセットコマンドを送信
        try:
            bus.write_i2c_block_data(SHT31_ADDRESS, 0x30, [0xA2])
            logger.info("✓ SHT31センサーへのコマンド送信成功")
            time.sleep(0.1)
            
            # ステータスレジスタの読み取りを試行
            try:
                bus.write_i2c_block_data(SHT31_ADDRESS, 0xF3, [0x2D])
                time.sleep(0.01)
                status = bus.read_i2c_block_data(SHT31_ADDRESS, 0x00, 3)
                logger.info(f"✓ SHT31ステータス読み取り成功: {[hex(x) for x in status]}")
                logger.info("🎉 SHT31センサーとの通信は正常です！")
                return True
                
            except Exception as e:
                logger.warning(f"ステータス読み取りエラー: {e}")
                logger.info("センサーは検出されましたが、完全な通信に問題があります")
                return False
                
        except Exception as e:
            logger.error(f"✗ SHT31センサーとの通信エラー: {e}")
            logger.error("センサーが接続されていないか、アドレスが間違っています")
            return False
            
    except Exception as e:
        logger.error(f"✗ I2Cバスへの接続エラー: {e}")
        logger.error("I2Cが有効になっていない可能性があります")
        return False
    finally:
        try:
            bus.close()
        except:
            pass

def scan_i2c_devices():
    """I2Cバス上のすべてのデバイスをスキャンする"""
    logger.info("I2Cバス上のデバイスをスキャンしています...")
    
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
            if SHT31_ADDRESS in found_devices:
                logger.info("🎯 SHT31センサー (0x44) が発見されました！")
            else:
                logger.warning("SHT31センサー (0x44) は発見されませんでした")
        else:
            logger.warning("I2Cデバイスが発見されませんでした")
            
        return found_devices
        
    except Exception as e:
        logger.error(f"I2Cスキャンエラー: {e}")
        return []
    finally:
        try:
            bus.close()
        except:
            pass

def check_i2c_permissions():
    """I2C権限を確認する"""
    import os
    import grp
    
    logger.info("I2C権限を確認しています...")
    
    # I2Cデバイスファイルの存在確認
    i2c_devices = ["/dev/i2c-0", "/dev/i2c-1", "/dev/i2c-20", "/dev/i2c-21"]
    existing_devices = [dev for dev in i2c_devices if os.path.exists(dev)]
    
    if existing_devices:
        logger.info(f"I2Cデバイス: {existing_devices}")
    else:
        logger.error("I2Cデバイスが見つかりません")
        return False
    
    # ユーザーのi2cグループ所属確認
    try:
        user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        if 'i2c' in user_groups:
            logger.info("✓ ユーザーはi2cグループに所属しています")
            return True
        else:
            logger.error("✗ ユーザーがi2cグループに所属していません")
            logger.info("解決方法: sudo usermod -a -G i2c $USER")
            return False
    except Exception as e:
        logger.error(f"グループ確認エラー: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== SHT31センサー通信テスト ===")
    
    # 1. 権限確認
    check_i2c_permissions()
    print()
    
    # 2. I2Cデバイススキャン
    devices = scan_i2c_devices()
    print()
    
    # 3. SHT31センサー通信テスト
    success = test_i2c_connection()
    print()
    
    if success:
        logger.info("🎉 すべてのテストが成功しました！")
        logger.info("SHT31.pyを通常モードで実行できます:")
        logger.info("python3 SHT31.py --interval 10")
    else:
        logger.info("❌ センサー通信に問題があります")
        logger.info("テストモードで実行してください:")
        logger.info("python3 SHT31.py --test --interval 5")