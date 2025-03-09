import toml
import time
import os

# 定义一个类来管理游戏状态
class Game:
    def __init__(self):
        # 加载基础配置文件
        self.config = self.load_toml("keyword/foundation.toml")
        self.story = self.load_toml("keyword/story.toml")
        self.endings = self.load_toml("keyword/endings.toml")
        self.save_file = "save.toml"  # 存档文件名

        # 初始化游戏状态
        self.current_chapter = self.config["current_state"]["current_chapter"]
        self.pad = self.config["current_state"]["pad"]
        self.character_name = self.config["character"]["character_name"]

        # 如果缺少键，打印警告信息
        if "current_chapter" not in self.config.get("current_state", {}):
            print("警告：'current_chapter' 键缺失，使用默认值 'chapter1'。")
            self.current_chapter = "chapter1"
        if "pad" not in self.config.get("current_state", {}):
            print("警告：'pad' 键缺失，使用默认值 0。")
            self.pad = 0
        if "character_name" not in self.config.get("character", {}):
            print("警告：'character_name' 键缺失，使用默认值 '神秘角色'。")
            self.character_name = "神秘角色"

    def load_toml(self, file_path):
        """加载 TOML 文件"""
        with open(file_path, "r", encoding="utf-8") as file:
            return toml.load(file)

    def save_game(self):
        """保存游戏进度到 TOML 文件"""
        save_data = {
            "current_chapter": self.current_chapter,
            "pad": self.pad
        }
        with open(self.save_file, "w", encoding="utf-8") as file:
            toml.dump(save_data, file)
        print("游戏已保存！")

    def load_game(self):
        """加载游戏进度"""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r", encoding="utf-8") as file:
                save_data = toml.load(file)
                self.current_chapter = save_data["current_chapter"]
                self.pad = save_data["pad"]
            print("游戏加载成功！")
        else:
            print("没有找到存档文件，开始新游戏。")

    def show_intro(self):
        """显示游戏介绍"""
        print(self.config["intro"])
        input("按回车键继续...")

    def show_story(self, chapter):
        """显示剧情"""
        for line in self.story[chapter]["lines"]:
            print(line)
            time.sleep(0.5)
        self.show_choices(chapter)

    def show_choices(self, chapter):
        """显示选择菜单"""
        choices = self.story[chapter]["choices"]
        for idx, choice in enumerate(choices, start=1):
            print(f"{idx}. {choice['text']}")
        while True:
            try:
                print("请输入选项编号：")
                choice_idx = int(input()) - 1
                if 0 <= choice_idx < len(choices):
                    self.handle_choice(chapter, choices[choice_idx])
                    break
                else:
                    print("无效的选项编号，请重新输入。")
            except ValueError:
                print("请输入一个有效的数字编号。")

    def handle_choice(self, chapter, choice):
        """处理玩家选择"""
        self.pad += choice["pad_change"]
        self.current_chapter = choice["next_chapter"]
        if self.current_chapter in self.endings:
            self.show_ending(self.current_chapter)
        else:
            self.show_story(self.current_chapter)

    def show_ending(self, ending_key):
        """显示结局"""
        ending = self.endings[ending_key]
        for line in ending["lines"]:
            print(line)
            time.sleep(0.5)
        print("游戏结束！")
        self.save_game()
        self.ask_restart()  # 询问用户是否重新开始

    def ask_restart(self):
        """询问用户是否重新开始游戏"""
        print("是否重新开始游戏？(y/n)")
        restart = input().strip().lower()
        if restart == "y":
            self.reset_game()  # 重置游戏状态并重新开始
        else:
            print("感谢游玩，再见！")
            exit()  # 退出程序

    def reset_game(self):
        """重置游戏状态"""
        self.current_chapter = "chapter1"  # 重置到初始章节
        self.pad = 0  # 重置 PAD 值
        self.save_game()  # 保存重置后的状态
        print("游戏已重置，重新开始游戏。")
        self.run()  # 重新开始游戏

    def run(self):
        """运行游戏"""
        self.load_game()
        self.show_intro()
        # 检查当前章节是否是结局
        if self.current_chapter in self.endings:
            self.show_ending(self.current_chapter)
        else:
            self.show_story(self.current_chapter)

# 主程序入口
if __name__ == "__main__":
    game = Game()
    game.run()
