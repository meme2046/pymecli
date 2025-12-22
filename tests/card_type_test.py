from douzero.env.move_detector import get_move_type
from utils.card import cards_to_env

# 测试"AAA3"牌型识别
cards_str = "AAA3"
cards_env = cards_to_env(cards_str)

print(f"牌面: {cards_str}")
print(f"数字编码: {cards_env}")

# 获取牌型信息
move_type = get_move_type(cards_env)
print(f"牌型信息: {move_type}")
