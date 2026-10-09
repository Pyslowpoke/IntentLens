import type { Metadata } from 'next';
import './globals.css';
import './brand.css';
import './studio.css';
import './evidence.css';
export const metadata: Metadata={title:'观意 IntentLens · 意图驱动的数据分析工作台',description:'理解分析意图，生成清晰视图，让每一步判断有据可循。'};
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="zh-CN"><body>{children}</body></html>; }
