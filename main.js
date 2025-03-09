const fs = require('fs');
const toml = require('toml');
const readline = require('readline');

class Game {
  constructor() {
    this.config = this.loadTOML('keyword/foundation.toml');
    this.story = this.loadTOML('keyword/story.toml');
    this.endings = this.loadTOML('keyword/endings.toml');
    this.saveFile = 'save.toml';

    this.currentChapter = this.config.current_state?.current_chapter || 'chapter1';
    this.pad = this.config.current_state?.pad || 0;
    this.characterName = this.config.character?.character_name || '神秘角色';

    this.checkMissingKeys();
  }

  checkMissingKeys() {
    const warnings = [];
    if (!this.config.current_state?.current_chapter) {
      warnings.push("'current_chapter' 键缺失，使用默认值 'chapter1'");
      this.currentChapter = 'chapter1';
    }
    if (!this.config.current_state?.pad) {
      warnings.push("'pad' 键缺失，使用默认值 0");
      this.pad = 0;
    }
    if (!this.config.character?.character_name) {
      warnings.push("'character_name' 键缺失，使用默认值 '神秘角色'");
      this.characterName = '神秘角色';
    }
    warnings.forEach(warning => console.warn(warning));
  }

  loadTOML(filePath) {
    try {
      const data = fs.readFileSync(filePath, 'utf-8');
      return toml.parse(data);
    } catch (error) {
      console.error(`无法加载TOML文件: ${filePath}`);
      throw error;
    }
  }

  saveGame() {
    const saveData = {
      current_chapter: this.currentChapter,
      pad: this.pad
    };
    fs.writeFileSync(this.saveFile, toml.stringify(saveData), 'utf-8');
    console.log('游戏已保存！');
  }

  loadGame() {
    if (fs.existsSync(this.saveFile)) {
      const saveData = toml.parse(fs.readFileSync(this.saveFile, 'utf-8'));
      this.currentChapter = saveData.current_chapter;
      this.pad = saveData.pad;
      console.log('游戏加载成功！');
    } else {
      console.log('没有找到存档文件，开始新游戏。');
    }
  }

  showIntro() {
    console.log(this.config.intro);
    this.waitForInput();
  }

  showStory(chapter) {
    this.story[chapter].lines.forEach(line => {
      console.log(line);
      setTimeout(() => {}, 500); // 0.5秒延迟
    });
    this.showChoices(chapter);
  }

  showChoices(chapter) {
    const choices = this.story[chapter].choices;
    choices.forEach((choice, index) => {
      console.log(`${index + 1}. ${choice.text}`);
    });

    this.waitForValidInput((input) => {
      const choiceIdx = parseInt(input) - 1;
      if (0 <= choiceIdx < choices.length) {
        this.handleChoice(chapter, choices[choiceIdx]);
      } else {
        console.log('无效的选项编号，请重新输入。');
        this.showChoices(chapter);
      }
    });
  }

  handleChoice(chapter, choice) {
    this.pad += choice.pad_change;
    this.currentChapter = choice.next_chapter;

    if (this.currentChapter in this.endings) {
      this.showEnding(this.currentChapter);
    } else {
      this.showStory(this.currentChapter);
    }
  }

  showEnding(endingKey) {
    this.endings[endingKey].lines.forEach(line => {
      console.log(line);
      setTimeout(() => {}, 500);
    });
    console.log('游戏结束！');
    this.saveGame();
    this.askRestart();
  }

  askRestart() {
    console.log('是否重新开始游戏？(y/n)');
    this.waitForInput((input) => {
      input = input.trim().toLowerCase();
      if (input === 'y') {
        this.resetGame();
      } else {
        console.log('感谢游玩，再见！');
        process.exit();
      }
    });
  }

  resetGame() {
    this.currentChapter = 'chapter1';
    this.pad = 0;
    this.saveGame();
    console.log('游戏已重置，重新开始游戏。');
    this.run();
  }

  run() {
    this.loadGame();
    this.showIntro();

    if (this.currentChapter in this.endings) {
      this.showEnding(this.currentChapter);
    } else {
      this.showStory(this.currentChapter);
    }
  }

  waitForInput(callback) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    rl.question('', (answer) => {
      callback(answer);
      rl.close();
    });
  }
}

if (require.main === module) {
  new Game().run();
}
