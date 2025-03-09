import toml
import time
import os
import logging
import re

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("game.log"),
        #logging.StreamHandler()
    ]
)

class Game:
    def __init__(self):
        logging.info("初始化游戏...")
        # 加载配置文件
        self.config = self.load_toml("keyword/foundation.toml")
        self.story = self.load_toml("keyword/story.toml")
        self.endings = self.load_toml("keyword/endings.toml")
        self.save_file = "save.toml"

        # 初始化游戏状态
        self.current_chapter = self.config["current_state"].get("current_chapter", "chapter1")
        self.pad = self.config["current_state"].get("pad", 0)
        self.character_name = self.config["character"].get("character_name", "神秘角色")

    # ... [其他方法保持不变，确保 show_intro 方法存在] ...

    def load_toml(self, file_path):
        """加载 TOML 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:  # 打开文件
                return toml.load(file)  # 使用 toml 模块加载文件内容并返回
        except FileNotFoundError:
            logging.error(f"文件未找到: {file_path}")
            raise
        except toml.TomlDecodeError:
            logging.error(f"TOML 文件格式错误: {file_path}")
            raise

    def save_game(self):
        """保存游戏进度到 TOML 文件"""
        save_data = {  # 定义要保存的数据
            "current_chapter": self.current_chapter,  # 当前章节
            "pad": self.pad  # 当前 PAD 值
        }
        try:
            with open(self.save_file, "w", encoding="utf-8") as file:  # 打开存档文件
                toml.dump(save_data, file)  # 将数据保存到文件
            logging.info("游戏已保存！")
        except Exception as e:
            logging.error(f"保存游戏失败: {e}")

    def load_game(self):
        """加载游戏进度"""
        if os.path.exists(self.save_file):  # 检查存档文件是否存在
            try:
                with open(self.save_file, "r", encoding="utf-8") as file:  # 打开存档文件
                    save_data = toml.load(file)  # 加载存档数据
                    self.current_chapter = save_data.get("current_chapter", "chapter1")  # 更新当前章节，默认为 "chapter1"
                    self.pad = save_data.get("pad", 0)  # 更新 PAD 值，默认为 0
                logging.info("游戏加载成功！")
            except Exception as e:
                logging.error(f"加载游戏失败: {e}")
        else:
            logging.info("没有找到存档文件，开始新游戏。")

    def show_story(self, chapter):
        """显示剧情并处理动态对话"""
        logging.info(f"显示剧情: {chapter}")
        if chapter in self.endings:
            self.show_ending(chapter)
            return
    
        try:
            # 基础对话必须存在
            lines = self.story[chapter]["lines"]  # 确保此行存在
            character_name = self.character_name
        except KeyError as e:
            logging.error(f"章节内容缺失: {e}")
            self.ask_restart()
            return

        # 动态对话覆盖逻辑（直接覆盖基础对话）
        if "pad_dialogues" in self.story[chapter]:
            for dialogue in self.story[chapter]["pad_dialogues"]:
                if self.is_in_range(self.pad, dialogue["range"]):
                    lines = dialogue["lines"]  # 覆盖基础对话
                    break  # 使用第一个匹配项

        # 显示对话
        for line in lines:
            print(line.replace("{character_name}", character_name))
            time.sleep(0.5)

        # 显示选择菜单
        self.show_choices(chapter)

    # ... [其他方法保持不变] ...

    def is_in_range(self, value, range_str):
        """检查值是否在指定范围内，支持区间和不等式"""
        # 处理不等式，例如 "pad >=5"
        inequality_match = re.match(r"pad\s*(>=|<=|>|<)\s*(-?\d+|inf)", range_str)
        if inequality_match:
            op = inequality_match.group(1)
            num_str = inequality_match.group(2)
            num = self.parse_number(num_str)
            if op == '>=':
                return value >= num
            elif op == '<=':
                return value <= num
            elif op == '>':
                return value > num
            elif op == '<':
                return value < num
            else:
                return False

        # 处理区间，例如 "(5, inf)" 或 "[0,5]"
        interval_match = re.match(r"^([\(\[])(-?\d+|inf|∞|-∞),\s*(-?\d+|inf|∞|-∞)([\)\]])$", range_str)
        if interval_match:
            start_bracket, start_str, end_str, end_bracket = interval_match.groups()
            start = self.parse_number(start_str)
            end = self.parse_number(end_str)
            left_open = (start_bracket == '(')
            right_open = (end_bracket == ')')
            left_cond = (value > start) if left_open else (value >= start)
            right_cond = (value < end) if right_open else (value <= end)
            return left_cond and right_cond

        # 处理其他格式，如 "pad ∈ (-∞, -5)"
        if '∈' in range_str:
            range_part = re.search(r"\(-∞,\s*(-?\d+)\)", range_str)
            if range_part:
                end = float(range_part.group(1))
                return value < end

        logging.warning(f"无法解析的范围字符串: {range_str}")
        return False

    def parse_number(self, s):
        """将字符串转换为数字，处理inf/-inf"""
        if s in ['inf', '∞']:
            return float('inf')
        elif s in ['-inf', '-∞']:
            return float('-inf')
        else:
            return float(s)

    def handle_choice(self, chapter, choice):
        """处理玩家选择并钳制PAD值"""
        try:
            pad_change = choice.get("pad_change", 0)
            if not isinstance(pad_change, (int, float)):
                logging.warning("PAD变更值格式错误，使用默认值0。")
                pad_change = 0
            self.pad += pad_change
            # 钳制PAD值在-100到100之间
            self.pad = max(min(self.pad, 100), -100)
            self.current_chapter = choice["next_chapter"]
        except KeyError as e:
            logging.error(f"选择项缺少必要字段: {e}")
            self.ask_restart()
            return

        if self.current_chapter in self.endings:
            self.show_ending(self.current_chapter)
        else:
            self.show_story(self.current_chapter)

    def show_choices(self, chapter):
        """显示选择菜单"""
        logging.info(f"显示选择菜单: {chapter}")
        try:
            choices = self.story[chapter]["choices"]  # 获取当前章节的选择列表
        except KeyError:
            logging.error(f"章节选择列表缺失: {chapter}")
            print("章节选择列表缺失，游戏无法继续。")
            self.ask_restart()
            return

        max_attempts = 3  # 最大尝试次数
        attempts = 0

        while attempts < max_attempts:
            try:
                for idx, choice in enumerate(choices, start=1):  # 遍历选择列表
                    print(f"{idx}. {choice['text']}")  # 打印选择编号和文本
                choice_idx = int(input("请输入选项编号：")) - 1  # 获取用户输入并转换为整数（索引从 0 开始）
                if 0 <= choice_idx < len(choices):  # 检查输入是否在有效范围内
                    self.handle_choice(chapter, choices[choice_idx])  # 处理用户选择
                    break
                else:
                    logging.warning("无效的选项编号，用户输入错误。")
                    print("无效的选项编号，请重新输入。")
            except ValueError:
                logging.warning("用户输入非数字。")
                print("请输入有效的数字编号。")
            attempts += 1
        else:
            logging.info("用户输入错误次数过多，自动退出游戏。")
            print("输入错误次数过多，自动退出游戏。")
            self.ask_restart()
    def handle_choice(self, chapter, choice):
        """处理玩家选择"""
        logging.info(f"处理玩家选择: {choice['text']}")
        try:
            pad_change = choice["pad_change"]
            if not isinstance(pad_change, (int, float)):
                logging.warning("PAD变更值格式错误，使用默认值0。")
                self.pad += 0
            else:
                self.pad += pad_change
            self.current_chapter = choice["next_chapter"]
        except KeyError as e:
            logging.error(f"选择项格式错误，缺少必要字段: {e}")
            print("选择项格式错误，游戏无法继续。")
            self.ask_restart()
            return  # 提前返回，避免继续执行后续逻辑

        # 检查当前章节是否是结局
        if self.current_chapter in self.endings:
            self.show_ending(self.current_chapter)
        else:
            self.show_story(self.current_chapter)  # 显示当前章节
    def show_ending(self, ending_key):
        """显示结局"""
        logging.info(f"显示结局: {ending_key}")
        try:
            ending = self.endings[ending_key]["lines"]
            logging.debug(f"结局对话: {ending}")
        except KeyError:
            logging.error(f"结局内容缺失: {ending_key}")
            ending = ["游戏结束！"]
    
        for line in ending:
            print(line.replace("{character_name}", self.character_name))
            time.sleep(0.5)
    
        print("游戏结束！")
        self.save_game()
        self.ask_restart()
    def ask_restart(self):
        """询问用户是否重新开始游戏"""
        restart = input("是否重新开始游戏？(y/n) ").strip().lower()
        if restart in ["y", "yes", "是"]:
            self.reset_game()  # 重置游戏
        else:
            print("感谢游玩，再见！")
            logging.info("游戏结束，用户选择退出。")
            exit()  # 退出程序
    def reset_game(self):
        """重置游戏状态"""
        logging.info("重置游戏状态...")
        self.current_chapter = "chapter1"  # 重置当前章节为初始章节
        self.pad = 0  # 重置 PAD 值为 0
        self.save_game()  # 保存重置后的游戏状态
        print("游戏已重置，重新开始游戏。")
        self.run()  # 重新运行游戏

    def show_intro(self):
        """显示游戏介绍"""
        try:
            print(self.config["intro"]["text"])  # 注意此处字段名应为 "text"
        except KeyError:
            logging.warning("游戏介绍缺失，使用默认内容。")
            print("游戏介绍缺失，使用默认内容。")
        input("按回车键继续...")

    def run(self):
        """运行游戏"""
        logging.info("游戏开始运行...")
        self.load_game()
        self.show_intro()  # 确保此行存在
        if self.current_chapter in self.endings:
            self.show_ending(self.current_chapter)
        else:
            self.show_story(self.current_chapter)

if __name__ == "__main__":
    game = Game()
    game.run()
