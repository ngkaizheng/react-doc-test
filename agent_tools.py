import sys
import os

def get_component_spec_xml(component_name):
    base_dir = os.path.join(os.getcwd(), "src", "components", "shared-ui")
    pure_name = component_name.replace(".tsx", "")
    filename = f"{pure_name}.tsx"
    file_path = os.path.join(base_dir, pure_name, filename)

    if not os.path.exists(file_path):
        return f"<error>Component '{pure_name}' not found.</error>"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        spec_lines = []
        is_extracting_props = False
        
        # 智能提取：只抓取 import、Interface/Props 定义以及组件声明头部
        for line in lines:
            # 1. 抓取顶部的注释（通常包含你的使用说明和 Few-shot）
            if line.strip().startswith("/**") or line.strip().startswith("*") or line.strip().startswith("*/"):
                spec_lines.append(line)
                continue
                
            # 2. 开始抓取 Interface 或 Type
            if "interface " in line or "type " in line:
                is_extracting_props = True
                
            if is_extracting_props:
                spec_lines.append(line)
                # 当遇到接口闭合的括号时，结束这一段的抓取
                if line.strip() == "}":
                    is_extracting_props = False
                    spec_lines.append("\n") # 留点空行
                    
            # 3. 抓取组件的导出声明（让 AI 知道组件名和基础入参形式）
            if f"export const {pure_name}" in line:
                spec_lines.append(line)
                spec_lines.append("  // ... [内部具体渲染逻辑已略去] ...\n")
                break # 后面的具体 HTML 渲染和逻辑就不要了
                
        spec_content = "".join(spec_lines).strip()
        
        # 如果什么都没提取到（比如没写 interface），就降级返回前 40 行
        if not spec_content:
            spec_content = "".join(lines[:40]) + "\n// ... [后面内容已截断] ..."

        # 返回完美的结构化 XML 说明书
        xml_output = (
            f"<component_specification>\n"
            f"  <name>{pure_name}</name>\n"
            f"  <api_interface><![CDATA[\n{spec_content}\n]]></api_interface>\n"
            f"</component_specification>"
        )
        return xml_output
        
    except Exception as e:
        return f"<error>Failed to read component: {str(e)}</error>"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comp_name = sys.argv[1]
        print(get_component_spec_xml(comp_name))
    else:
        print("<error>Missing argument: component_name</error>")