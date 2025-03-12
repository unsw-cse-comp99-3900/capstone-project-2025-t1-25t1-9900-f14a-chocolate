import pandas as pd
import sqlite3



def csv2db(csv_file='qs-world-rankings-2025.csv', db_file='qs-world-rankings-2025.db', table_name='qs2025'):
    # 读取CSV文件
    df = pd.read_csv(csv_file)

    # 连接（或创建）SQLite数据库
    conn = sqlite3.connect(db_file)

    # 将数据写入数据库
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    
    query = f'SELECT * FROM {table_name} LIMIT 5'

    result = pd.read_sql_query(query, conn)

    # 打印前五行数据
    print(result)


    # 关闭连接
    conn.close()

def del_table(db_file='qs-world-rankings-2025.db', table_name='qs2025'):
    """
    删除指定数据库中的表（如果表存在）。
    
    参数：
        db_file (str): SQLite数据库文件路径。
        table_name (str): 要删除的表名。
    """
    # 连接数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 删除表（如果存在）
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        print(f"Table '{table_name}' has been deleted (if it existed).")
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
    finally:
        # 关闭连接
        cursor.close()
        conn.close()


def show_database(db_file='qs-world-rankings-2025.db'):
    # 连接（或创建）SQLite数据库
    conn = sqlite3.connect(db_file)

    # 查询存在的表
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    result = pd.read_sql_query(query, conn)
    print(result)
     
    # 关闭连接
    conn.close()

#重命名表
def rename_table(db_file='qs-world-rankings-2025.db', old_table_name='qs2025', new_table_name='qs_rank_2025'):
    # 连接（或创建）SQLite数据库
    conn = sqlite3.connect(db_file)

    # 重命名表
    conn.execute(f'ALTER TABLE {old_table_name} RENAME TO {new_table_name}')

    # 查询存在的表
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    result = pd.read_sql_query(query, conn)
    print(result)
     
    # 关闭连接
    conn.close()
    
def subject2csv():
    xlsx_file = '/home/workstation/workspace/AchievaSearch/table_dataset/2024 QS by Subject.xlsx'
    #读取xlsx文件，每一个sheet对应一个学科，将学科名作为csv文件名
    df = pd.read_excel(xlsx_file, sheet_name=None)
    for subject, data in df.items():
        #把subject中的空格替换为下划线, &替换为and, -替换为. 
        subject = subject.replace(' ', '_').replace('&', 'and').replace('-', '.').replace('$', '')
        #把data 2024 column改名为2024_Rank, 2023 column改名为2023_Rank
        data.rename(columns={'2024': '2024_Rank', '2023': '2023_Rank'}, inplace=True)
        data.to_csv(f'subject/{subject}.csv', index=False)
     
#查询某表前五行
def show_table(db_file='education_info.db', table_name='qs_rank_2025'):
    # 连接（或创建）SQLite数据库
    conn = sqlite3.connect(db_file)

    query = f'SELECT * FROM {table_name} LIMIT 5'
    result = pd.read_sql_query(query, conn)
    print(result)
    
    
achieva_db = 'education_info.db'
# UQ_2025_csv = 'UQ_2025.csv'
qs2025_csv = 'qs-world-rankings-2025.csv'

qs_table_name = 'qs_rank_university'
# uq_course_requirement_table_name = 'UQ_university_of_queensland_course_requirement'


# csv2db(csv_file=qs2025_csv, db_file=achieva_db, table_name=qs_table_name)
# # csv2db(csv_file=UQ_2025_csv, db_file=achieva_db, table_name=uq_course_requirement_table_name)

# show_database(db_file=achieva_db)


#重命名qs_rank_2025为qs_rank_university
# rename_table(db_file='education_info.db', old_table_name='qs_rank_2025', new_table_name='qs_rank_university')
# show_table(db_file='education_info.db')

#删除 qs_rank_History of Art
# del_table(db_file='education_info.db', table_name='qs_rank_2025')
# show_table(db_file='education_info.db')


# show_table(db_file='education_info.db', table_name='qs_rank_History_of_Art')

# subject2csv()

achieva_db = 'education_info.db'

# #读取/home/workstation/workspace/AchievaSearch/table_dataset/subject下所有的csv文件
# csv_files = '/home/workstation/workspace/AchievaSearch/table_dataset/subject'
# import os
# for file in os.listdir(csv_files):
#     if file.endswith('.csv'):
#             csv_file = os.path.join(csv_files, file)
#             subject=file.split('.')[0]
#             csv2db(csv_file=csv_file, db_file=achieva_db, table_name=f'qs_rank_{subject}')

# show_database(db_file=achieva_db)


result = pd.read_sql_query('SELECT * FROM qs_rank_university WHERE "Location" LIKE "%Australia%" LIMIT 10;', sqlite3.connect(achieva_db))
print(result)