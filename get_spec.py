# get_spec.py
import sys
import os
import json

def get_component_xml_from_spec(component_name):
    spec_path = os.path.join(os.getcwd(), ".agent-ui-spec.json")
    
    # 1. 检查 spec.json 是否存在
    if not os.path.exists(spec_path):
        return f"<error>未找到规范文件 .agent-ui-spec.json，请先在终端运行 npm run build:spec 生成。</error>"

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_data = json.load(f)
            
        # 2. 匹配组件名称（不区分大小写，且去掉可能误传的 .tsx 后缀）
        target_name = component_name.replace(".tsx", "").lower()
        matched_component = None
        
        for item in spec_data:
            if item.get("name", "").lower() == target_name:
                matched_component = item
                break
                
        if not matched_component:
            return f"<error>在规范文件中未找到组件 '{component_name}' 的资料。</error>"

        # 3. 💥 将 JSON 转换成 AI 最喜欢的、注意力极度集中的 XML 结构化格式
        name = matched_component.get("name")
        description = matched_component.get("description", "")
        examples = matched_component.get("examples", [])
        props = matched_component.get("props", [])

        # 拼接 Props 的格式化字符串
        props_str = ""
        for p in props:
            req_mark = " (必填)" if p.get("required") else " (可选)"
            desc = f" - {p.get('description')}" if p.get("description") else ""
            props_str += f"    - {p.get('name')}: `{p.get('type')}`{req_mark}{desc}\n"

        # 拼接 Examples 格式
        examples_str = ""
        for idx, ex in enumerate(examples):
            examples_str += f"  <example_case__{idx + 1}>\n<![CDATA[\n{ex}\n]]>\n  </example_case__{idx + 1}>\n"

        # 组合成最终返回给 VS Code Copilot 的完美 XML 燃料
        xml_output = (
            f"<component_specification>\n"
            f"  <component_name>{name}</component_name>\n"
            f"  <business_description>{description}</business_description>\n"
            f"  <available_props>\n{props_str}  </available_props>\n"
            f"  <few_shot_examples>\n{examples_str}  </few_shot_examples>\n"
            f"</component_specification>"
        )
        return xml_output

    except Exception as e:
        return f"<error>读取组件规范失败: {str(e)}</error>"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comp_name = sys.argv[1]
        print(get_component_xml_from_spec(comp_name))
    else:
        print("<error>请传入要查询的组件名称，例如: python get_spec.py Button</error>")