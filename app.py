from flask import Flask, render_template, request, send_file
import pandas as pd
import io

app = Flask(__name__)

MAPPINGS = {
    'google': {
        'Organization Name': '会社名',
        'Organization Title': '役職',
        'First Name': '氏名(名)',
        'Last Name': '氏名(姓)',
        'Address 1 - Street': '番地',
        'Address 1 - City': '市区町村',
        'Address 1 - Region': '都道府県',
        'Address 1 - Postal Code': '郵便番号',
        'Phone 1 - Value': '電話番号',
        'E-mail 1 - Value': 'メールアドレス'
    },
    'shopify': {
        'Default Address Company': '会社名',
        'First Name': '氏名(名)',
        'Last Name': '氏名(姓)',
        'Default Address Address1': '番地',
        'Default Address City': '市区町村',
        'Default Address Province Code': '都道府県',
        'Default Address Zip': '郵便番号',
        'Default Address Phone': '電話番号',
        'Email': 'メールアドレス'
    },
    'sent': {
        '会社名': '会社名',
        '肩書': '役職',
        'お名前（敬称省略）': '氏名(姓)',
        '郵便番号': '郵便番号',
        '住所１列目': '番地',
        '住所２列目': '市区町村',
        'メール': 'メールアドレス'
    }
}

def clean_data(df, category, mode):
    mapping = MAPPINGS.get(mode, MAPPINGS['google'])
    extracted = pd.DataFrame()
    
    # 必要な列の抽出
    for col_key, new_name in mapping.items():
        extracted[new_name] = df[col_key] if col_key in df.columns else ""
    
    # 空白削除・小文字統一
    extracted = extracted.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    if 'メールアドレス' in extracted.columns:
        extracted['メールアドレス'] = extracted['メールアドレス'].str.lower()

    # 組み合わせ項目の作成
    extracted['住所結合'] = (extracted['都道府県'].fillna('') + extracted['市区町村'].fillna(''))
    extracted['氏名結合'] = (extracted['氏名(姓)'].fillna('') + ' ' + extracted['氏名(名)'].fillna('')).str.strip()
    extracted['区分'] = category

    # ラベルやさん用の列定義
    output_columns = [
        '郵便番号', '住所結合', '番地', '会社名', '役職', '氏名結合', 
        '電話番号', 'メールアドレス', '区分', '氏名(姓)', '氏名(名)', 
        '都道府県', '市区町村'
    ]
    
    # 不足列の補完
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
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig', sep=None, engine='python')
                    cleaned_df = clean_data(df, category, mode)
                    all_data.append(cleaned_df)
                except Exception as e:
                    return f"エラー: {file.filename} の読み込みに失敗しました。{str(e)}"
        
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
