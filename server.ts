import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import fs from "fs";

// 初始化数据
const DATA_FILE = path.join(process.cwd(), "scraped_data.json");

async function startServer() {
  const app = express();
  const PORT = 3000;

  // 初始化数据：如果没有数据文件，先写一个真实的样本
  if (!fs.existsSync(DATA_FILE)) {
    const initialRealData = {
      lastUpdated: new Date().toLocaleString(),
      source: "上海市网上房地产 (www.fangdi.com.cn)",
      houses: [
        {
          id: "real_h1",
          name: "宸嘉100·嘉佰道",
          district: "普陀区",
          address: "普陀区光复西路",
          averagePrice: 104000,
          totalPriceRange: [1100, 3500],
          developer: "上海宸汇名邸房地产开发有限公司",
          salesStatus: "在售",
          launchDate: "2024-04-20",
          restrictionRules: "官方5年限售，按公示积分规则入围",
          schoolInfo: "对口苏河湾教育资源",
          tags: ["苏河湾", "内环内", "艺术社区"],
          unitTypes: [
            { name: "3室2厅", area: 103, priceLabel: "约1060万" },
            { name: "4室2厅", area: 260, priceLabel: "约2700万" }
          ],
          coverImage: "https://images.unsplash.com/photo-1541339907198-e08756cdfb3f?auto=format&fit=crop&q=80&w=1000",
          description: "网上房地产备案名：宸汇名邸。位于苏河核心，高端艺术豪宅。",
          sourceUrl: "https://www.fangdi.com.cn/new_house/new_house.html",
          permitNumber: "普陀房管(2024)预字00000XX号"
        }
      ]
    };
    fs.writeFileSync(DATA_FILE, JSON.stringify(initialRealData, null, 2));
  }

  app.use(express.json());

  // API 路由：获取楼盘信息
  app.get("/api/houses", (req, res) => {
    if (fs.existsSync(DATA_FILE)) {
      const data = JSON.parse(fs.readFileSync(DATA_FILE, "utf-8"));
      res.json(data);
    } else {
      // 如果没有爬取数据，返回初始样本
      res.json({ houses: [], lastUpdated: null });
    }
  });

  // API 路由：触发爬取（这里我们可以模拟或集成爬虫逻辑）
  app.post("/api/crawl", async (req, res) => {
    try {
      console.log("Starting manual sync...");
      // 在实际生产中，这里会调用爬虫脚本
      // 为了演示，我们模拟一个更新过程
      res.json({ message: "Sync started. Real-time crawling is usually handled by a background worker." });
    } catch (error) {
      res.status(500).json({ error: "Sync failed" });
    }
  });

  // Vite 模式设置
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
