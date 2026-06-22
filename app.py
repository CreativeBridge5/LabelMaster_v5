from flask import Flask, render_template, request, send_file
import pandas as pd
import io

app = Flask(__name__)

# マッピング定義
MAPPINGS = {
    'google': {
        'Organization Name': '会社名', 'Organization Title': '役職', 'First Name': '氏名(名)',
        'Last Name': '氏名(姓)', 'First Name1': '氏名結合', 'Address 1 - Street': '番地',
        'Address 1 - City': '市区町村', 'Address 1 - Region': '都道府県',
        'Address 1 - Postal Code': '郵便番号', 'Phone 1 - Value': '電話番号', 'E-mail 1 - Value': 'メールアドレス'
    },
    'shopify': {
        'Default Address Company': '会社名', 'First Name': '氏名(名)', 'Last Name': '氏名(姓)',
        'Default Address Address1': '番地', 'Default Address City': '市区町村',
        'Default Address Province Code': '都道府県', 'Default Address Zip': '郵便番号',
        'Default Address Phone': '電話番号', 'Email': 'メールアドレス'
    },
    'sent': {
        '会社名': '会社名', '肩書': '役職', 'お名前（敬称省略）': '氏名(姓)',
        '郵便番号': '郵便番号', '住所１列目': '番地', '住所２列目': '市区町村', '担当メール': 'メールアドレス'
    }
}

def clean_data(df, category, mode):
    mapping = MAPPINGS.get(mode, MAPPINGS['google'])
    
    # マッピングに基づいてデータを抽出
    result_data = {}
    for col_key, new_name in mapping.items():
        result_data[new_name] = df[col_key] if col_key in df.columns else ""
    
    extracted = pd.DataFrame(result_data)
    
    # 全角スペースや前後の空白を除去
    extracted = extracted.apply(lambda x: x.astype(str).str.strip().str.replace(' ', ' ') if x.dtype == "object" else x)
    
    # 住所結合 (都道府県 + 市区町村)
    pre = extracted['都道府県'] if '都道府県' in extracted.columns else ""
    city = extracted['市区町村'] if '市区町村' in extracted.columns else ""
    extracted['住所結合'] = (pre.replace('nan', '') + city.replace('nan', '')).str.strip()
    
    # 氏名結合 (姓 + 名)
    last = extracted['氏名(姓)'] if '氏名(姓)' in extracted.columns else ""
    first = extracted['氏名(名)'] if '氏名(名)' in extracted.columns else ""
    extracted['氏名結合'] = (last.replace('nan', '') + ' ' + first.replace('nan', '')).str.strip()
    
    extracted['区分'] = category

    # 出力用カラムの順序定義
    output_columns = [
        '郵便番号', '住所結合', '番地', '会社名', '役職', '氏名結合', 
        '電話番号', 'メールアドレス', '区分', '氏名(姓)', '氏名(名)', 
        '都道府県', '市区町村'
    ]
    
    # 存在しないカラムを埋める
    for col in output_columns:
        if col not in extracted.columns:
            extracted[col] = ""
            
    return extracted[output_columns]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        category = request.form.get('category', '未分類')
        mode = request.form.get('mode', 'google')
        
        all_data = []
        for file in files:
            if file.filename != '':
                # CSV読み込みの安定化（エンコーディングと区切り文字の指定）
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig', engine='python')
                except:
                    # UTF-8がダメな場合はcp932で再試行
                    file.seek(0)
                    df = pd.read_csv(file, encoding='cp932', engine='python')
                
                all_data.append(clean_data(df, category, mode))
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            output = io.StringIO()
            combined_df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                             mimetype='text/csv', as_attachment=True, download_name='print_labels.csv')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
