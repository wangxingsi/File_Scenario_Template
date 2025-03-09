const fs = require('fs');
const toml = require('toml');
const path = require('path');
const { createLogger, format, transports } = require('winston');

// 配置日志
const logger = createLogger({
    format: format.combine(
        format.timestamp(),
        format.printf(info => `${info.timestamp} - ${info.level} - ${info.message}`)
    ),
    transports: [
        new transports.File({ filename: 'game.log' })
    ]
});

// 游戏类
class Game {
    constructor() {
        logger.info('初始化游戏...');
        this.loadConfig('keyword/foundation.toml');
        this.loadStory('keyword/story.toml');
        this.loadEndings('keyword/endings.toml');
        this.loadGame();
        this.showIntro();
        this.run();
    }

    loadConfig(filePath) {
        this.config = this.loadTomlFile(filePath);
        this.currentChapter = this.config.current_state?.current_chapter || 'chapter1';
        this.pad = this.config.current_state?.pad || 0;
        this.characterName = this.config.character?.character_name || '神秘角色';
    }

    loadStory(filePath) {
        this.story = this.loadTomlFile(filePath);
    }

    loadEndings(filePath) {
        this.endings = this.loadTomlFile(filePath);
    }

    loadTomlFile(filePath) {
        try {
            const fileContent = fs.readFileSync(filePath, 'utf-8');
            return toml.parse(fileContent);
        } catch (error) {
            logger.error(`文件加载失败: ${filePath}`, error);
            throw new Error(`文件加载失败: ${filePath}`);
        }
    }

    saveGame() {
        const saveData = {
            currentChapter: this.currentChapter,
            pad: this.pad
        };
        fs.writeFileSync('save.toml', toml.stringify(saveData));
        logger.info('游戏已保存！');
    }

    loadGame() {
        if (fs.existsSync('save.toml')) {
            const saveData = this.loadTomlFile('save.toml');
            this.currentChapter = saveData.currentChapter || 'chapter1';
            this.pad = saveData.pad || 0;
            logger.info('游戏加载成功！');
        } else {
            logger.info('没有找到存档文件，开始新游戏。');
        }
    }

    showIntro() {
        try {
            logger.info('显示游戏介绍');
            console.log(this.config.intro.text);
        } catch (error) {
            logger.warn('游戏介绍缺失，使用默认内容。');
            console.log('游戏介绍缺失，使用默认内容。');
        }
        process.stdin.resume();
        process.stdin.on('data', () => {
            process.stdin.pause();
            this.run();
        });
    }

    run() {
        logger.info('游戏开始运行...');
        if (this.endings[this.currentChapter]) {
            this.showEnding(this.currentChapter);
        } else {
            this.showStory(this.currentChapter);
        }
    }

    showStory(chapter) {
        logger.info(`显示剧情: ${chapter}`);
        let lines = this.story[chapter].lines;
        if (this.story[chapter].pad_dialogues) {
            for (const dialogue of this.story[chapter].pad_dialogues) {
                if (this.isInRange(this.pad, dialogue.range)) {
                    lines = dialogue.lines;
                    break;
                }
            }
        }
        console.log(lines.replace(/\{character_name\}/g, this.characterName));
        this.showChoices(chapter);
    }

    showChoices(chapter) {
        logger.info(`显示选择菜单: ${chapter}`);
        const choices = this.story[chapter].choices;
        choices.forEach((choice, index) => {
            console.log(`${index + 1}. ${choice.text}`);
        });

        process.stdin.resume();
        process.stdin.on('data', (input) => {
            const choiceIdx = parseInt(input.toString().trim()) - 1;
            if (choiceIdx >= 0 && choiceIdx < choices.length) {
                this.handleChoice(chapter, choices[choiceIdx]);
            } else {
                console.log('无效的选项编号，请重新输入。');
                this.showChoices(chapter);
            }
            process.stdin.pause();
        });
    }

    handleChoice(chapter, choice) {
        logger.info(`处理玩家选择: ${choice.text}`);
        this.pad += choice.pad_change || 0;
        this.pad = Math.max(Math.min(this.pad, 100), -100);
        this.currentChapter = choice.next_chapter;

        if (this.endings[this.currentChapter]) {
            this.showEnding(this.currentChapter);
        } else {
            this.showStory(this.currentChapter);
        }
    }

    showEnding(endingKey) {
        logger.info(`显示结局: ${endingKey}`);
        const endingLines = this.endings[endingKey].lines;
        console.log(endingLines.replace(/\{character_name\}/g, this.characterName));
        console.log('游戏结束！');
        this.saveGame();
        this.askRestart();
    }

    askRestart() {
        logger.info('询问用户是否重新开始游戏');
        process.stdin.resume();
        process.stdin.on('data', (input) => {
            const restart = input.toString().trim().toLowerCase();
            if (['y', 'yes', '是'].includes(restart)) {
                this.resetGame();
            } else {
                console.log('感谢游玩，再见！');
                logger.info('游戏结束，用户选择退出。');
                process.exit(0);
            }
            process.stdin.pause();
        });
        console.log('是否重新开始游戏？(y/n) ');
    }

    resetGame() {
        logger.info('重置游戏状态...');
        this.currentChapter = 'chapter1';
        this.pad = 0;
        this.saveGame();
        console.log('游戏已重置，重新开始游戏。');
        this.run();
    }

    isInRange(value, rangeStr) {
        const match = rangeStr.match(/(\d+)\s*-\s*(\d+)/);
        if (match) {
            const start = parseInt(match[1], 10);
            const end = parseInt(match[2], 10);
            return value >= start && value <= end;
        }
        return false;
    }
}

// 主程序
if (require.main === module) {
    new Game();
}
