#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <regex>
#include <toml11/toml.hpp>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>

// 日志初始化
auto logger = spdlog::basic_logger_mt("game_log", "game.log");

// 游戏类
class Game {
public:
    Game() {
        logger->info("初始化游戏...");
        loadConfig("keyword/foundation.toml");
        loadStory("keyword/story.toml");
        loadEndings("keyword/endings.toml");
        loadGame();
        showIntro();
        run();
    }

private:
    toml::table config, story, endings;
    std::string currentChapter = "chapter1";
    int pad = 0;
    std::string characterName = "神秘角色";

    void loadConfig(const std::string& filePath) {
        config = loadTomlFile(filePath);
        currentChapter = config["current_state"].get<std::string>("current_chapter", "chapter1");
        pad = config["current_state"].get<int>("pad", 0);
        characterName = config["character"].get<std::string>("character_name", "神秘角色");
    }

    void loadStory(const std::string& filePath) {
        story = loadTomlFile(filePath);
    }

    void loadEndings(const std::string& filePath) {
        endings = loadTomlFile(filePath);
    }

    toml::table loadTomlFile(const std::string& filePath) {
        std::ifstream file(filePath);
        if (!file) {
            logger->error("文件未找到: {}", filePath);
            throw std::runtime_error("文件未找到: " + filePath);
        }
        toml::table table;
        file >> table;
        return table;
    }

    void saveGame() {
        toml::table saveData;
        saveData["current_chapter"] = currentChapter;
        saveData["pad"] = pad;

        std::ofstream file("save.toml");
        file << saveData;
        logger->info("游戏已保存！");
    }

    void loadGame() {
        if (std::ifstream file("save.toml")) {
            toml::table saveData;
            file >> saveData;
            currentChapter = saveData["current_chapter"].get<std::string>("chapter1");
            pad = saveData["pad"].get<int>(0);
            logger->info("游戏加载成功！");
        } else {
            logger->info("没有找到存档文件，开始新游戏。");
        }
    }

    void showIntro() {
        try {
            logger->info("显示游戏介绍");
            std::cout << config["intro"]["text"].get<std::string>() << std::endl;
        } catch (const std::exception& e) {
            logger->warn("游戏介绍缺失，使用默认内容。");
            std::cout << "游戏介绍缺失，使用默认内容。" << std::endl;
        }
        std::cin.ignore();
    }

    void run() {
        logger->info("游戏开始运行...");
        if (endings.contains(currentChapter)) {
            showEnding(currentChapter);
        } else {
            showStory(currentChapter);
        }
    }

    void showStory(const std::string& chapter) {
        logger->info("显示剧情: {}", chapter);
        std::string lines = story[chapter]["lines"].get<std::string>();
        std::string characterName = this->characterName;

        // 动态对话覆盖逻辑
        if (story[chapter].contains("pad_dialogues")) {
            auto padDialogues = story[chapter]["pad_dialogues"].as_array();
            for (const auto& dialogue : padDialogues) {
                auto range = dialogue["range"].get<std::string>();
                if (isInRange(pad, range)) {
                    lines = dialogue["lines"].get<std::string>();
                    break;
                }
            }
        }

        // 显示对话
        std::cout << std::regex_replace(lines, std::regex("\\{character_name\\}"), characterName) << std::endl;

        // 显示选择菜单
        showChoices(chapter);
    }

    void showChoices(const std::string& chapter) {
        logger->info("显示选择菜单: {}", chapter);
        auto choices = story[chapter]["choices"].as_array();
        for (size_t i = 0; i < choices.size(); ++i) {
            std::cout << i + 1 << ". " << choices[i]["text"].get<std::string>() << std::endl;
        }

        int choice;
        std::cin >> choice;
        if (choice < 1 || choice > choices.size()) {
            logger->error("无效的选项编号");
            std::cout << "无效的选项编号，请重新输入。" << std::endl;
            showChoices(chapter);
            return;
        }

        handleChoice(chapter, choices[choice - 1]);
    }

    void handleChoice(const std::string& chapter, const toml::node& choiceNode) {
        auto choice = choiceNode.as_table();
        try {
            pad += choice["pad_change"].get<int>(0);
            currentChapter = choice["next_chapter"].get<std::string>();
            pad = std::clamp(pad, -100, 100);  // 钳制 PAD 值
            logger->info("处理玩家选择: {}", choice["text"].get<std::string>());
        } catch (const std::exception& e) {
            logger->error("选择项格式错误: {}", e.what());
            std::cout << "选择项格式错误，游戏无法继续。" << std::endl;
            askRestart();
            return;
        }

        if (endings.contains(currentChapter)) {
            showEnding(currentChapter);
        } else {
            showStory(currentChapter);
        }
    }

    void showEnding(const std::string& endingKey) {
        logger->info("显示结局: {}", endingKey);
        std::string endingLines = endings[endingKey]["lines"].get<std::string>();
        std::cout << std::regex_replace(endingLines, std::regex("\\{character_name\\}"), characterName) << std::endl;
        std::cout << "游戏结束！" << std::endl;
        saveGame();
        askRestart();
    }

    void askRestart() {
        logger->info("询问用户是否重新开始游戏");
        std::string restart;
        std::cout << "是否重新开始游戏？(y/n) ";
        std::cin >> restart;
        if (restart == "y" || restart == "yes") {
            resetGame();
        } else {
            std::cout << "感谢游玩，再见！" << std::endl;
            logger->info("游戏结束，用户选择退出。");
            exit(0);
        }
    }

    void resetGame() {
        logger->info("重置游戏状态...");
        currentChapter = "chapter1";
        pad = 0;
        saveGame();
        std::cout << "游戏已重置，重新开始游戏。" << std::endl;
        run();
    }

    bool isInRange(int value, const std::string& rangeStr) {
        // 简单的范围解析逻辑
        std::regex rangeRegex(R"((\d+)\s*-\s*(\d+))");
        std::smatch match;
        if (std::regex_search(rangeStr, match, rangeRegex)) {
            int start = std::stoi(match[1].str());
            int end = std::stoi(match[2].str());
            return value >= start && value <= end;
        }
        return false;
    }
};

int main() {
    try {
        Game game;
    } catch (const std::exception& e) {
        logger->error("发生错误: {}", e.what());
        std::cerr << "发生错误: " << e.what() << std::endl;
    }
    return 0;
}
