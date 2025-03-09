#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <variant>
#include <chrono>
#include <thread>
#include <filesystem>

using namespace std;
using namespace std::chrono_literals;

// TOML解析相关类型定义
using TomlValue = std::variant<
    int,
    double,
    string,
    bool,
    std::map<string, TomlValue>,
    std::vector<TomlValue>
>;

namespace toml {
    using TomlMap = std::map<std::string, TomlValue>;
}

// TOML解析函数（简化版）
toml::Tompkin::Toml parse_toml(const string& filename) {
    ifstream file(filename);
    toml::Tompkin::Toml toml;
    file >> toml;
    return toml;
}

void save_toml(const string& filename, const toml::Tompkin::Toml& data) {
    ofstream file(filename);
    file << data;
}

class Game {
private:
    toml::Tompkin::Toml config;
    toml::Tompkin::Toml story;
    toml::Tompkin::Toml endings;
    string save_file = "save.toml";
    
    string current_chapter;
    int pad;
    string character_name;
    
    void load_default_values() {
        current_chapter = "chapter1";
        pad = 0;
        character_name = "神秘角色";
    }

public:
    Game() {
        // 加载配置文件
        config = parse_toml("keyword/foundation.toml");
        story = parse_toml("keyword/story.toml");
        endings = parse_toml("keyword/endings.toml");
        
        // 初始化游戏状态
        auto& current_state = config["current_state"];
        current_chapter = current_state.contains("current_chapter") 
                            ? current_state["current_chapter"].as<string>() 
                            : "chapter1";
        pad = current_state.contains("pad") 
              ? current_state["pad"].as<int>() 
              : 0;
        character_name = config["character"].contains("character_name") 
                          ? config["character"]["character_name"].as<string>() 
                          : "神秘角色";
        
        // 检查并设置默认值
        if (!config["current_state"].contains("current_chapter")) {
            cout << "警告：'current_chapter' 键缺失，使用默认值 'chapter1'。" << endl;
            current_chapter = "chapter1";
        }
        if (!config["current_state"].contains("pad")) {
            cout << "警告：'pad' 键缺失，使用默认值 0。" << endl;
            pad = 0;
        }
        if (!config["character"].contains("character_name")) {
            cout << "警告：'character_name' 键缺失，使用默认值 '神秘角色'。" << endl;
            character_name = "神秘角色";
        }
    }

    void save_game() {
        toml::Tompkin::Toml save_data;
        save_data["current_chapter"] = current_chapter;
        save_data["pad"] = pad;
        save_toml(save_file, save_data);
        cout << "游戏已保存！" << endl;
    }

    void load_game() {
        if (filesystem::exists(save_file)) {
            auto save_data = parse_toml(save_file);
            current_chapter = save_data["current_chapter"].as<string>();
            pad = save_data["pad"].as<int>();
            cout << "游戏加载成功！" << endl;
        } else {
            cout << "没有找到存档文件，开始新游戏。" << endl;
            load_default_values();
        }
    }

    void show_intro() {
        cout << config["intro"].as<string>() << endl;
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        cout << "按回车键继续..." << endl;
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
    }

    void show_story(const string& chapter) {
        for (const auto& line : story[chapter]["lines"]) {
            cout << line.as<string>() << endl;
            this_thread::sleep_for(500ms);
        }
        show_choices(chapter);
    }

    void show_choices(const string& chapter) {
        const auto& choices = story[chapter]["choices"];
        for (size_t i = 0; i < choices.size(); ++i) {
            cout << i + 1 << ". " << choices[i]["text"].as<string>() << endl;
        }
        
        int choice_idx;
        while (true) {
            cout << "请输入选项编号：" << endl;
            cin >> choice_idx;
            
            if (cin.fail() || choice_idx < 1 || choice_idx > choices.size()) {
                cin.clear();
                cin.ignore(numeric_limits<streamsize>::max(), '\n');
                cout << "无效的选项编号，请重新输入。" << endl;
            } else {
                handle_choice(chapter, choices[choice_idx - 1]);
                break;
            }
        }
    }

    void handle_choice(const string& chapter, const toml::Tompkin::Toml& choice) {
        pad += choice["pad_change"].as<int>();
        current_chapter = choice["next_chapter"].as<string>();
        
        if (endings.count(current_chapter)) {
            show_ending(current_chapter);
        } else {
            show_story(current_chapter);
        }
    }

    void show_ending(const string& ending_key) {
        for (const auto& line : endings[ending_key]["lines"]) {
            cout << line.as<string() << endl;
            this_thread::sleep_for(500ms);
        }
        cout << "游戏结束！" << endl;
        save_game();
        ask_restart();
    }

    void ask_restart() {
        char restart;
        cout << "是否重新开始游戏？(y/n)" << endl;
        cin >> restart;
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        
        if (restart == 'y') {
            reset_game();
        } else {
            cout << "感谢游玩，再见！" << endl;
            exit(0);
        }
    }

    void reset_game() {
        load_default_values();
        save_game();
        run();
    }

    void run() {
        load_game();
        show_intro();
        
        if (endings.count(current_chapter)) {
            show_ending(current_chapter);
        } else {
            show_story(current_chapter);
        }
    }
};

int main() {
    Game game;
    game.run();
    return 0;
}
