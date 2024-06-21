import re
import emojis
import unicodedata
import pandas as pd

from typing import List, Dict
import modules.regex_patterns as RegPattern
import modules.user_object_defined as udt


def fix_spacing(ptext: str) -> str:
    """
    Thêm khoảng trắng trước chữ cái hoa và dấu câu nếu chưa có

    Args:
        ptext (str): comment

    Returns:
        [str]: comment đã được thêm khoảng trắng trước chữ cái hoa và dấu câu
    """
    if isinstance(ptext, str):
        # Thêm khoảng trắng trước chữ cái hoa và dấu câu nếu chưa có
        ptext = re.sub(r"(?<!\s)([A-Z])", r" \1", ptext)
        ptext = re.sub(r"(?<!\s)([:;,.\?])", r" \1", ptext)
        ptext = ptext.strip()
    return ptext


def containsURL(ptext: str) -> (int):
    """
    Dùng kiểm tra ptext có chứa url hay ko

    Args:
        ptext (str): comment

    Returns:
        [int]: 1 có 0 ko
    """
    flag = re.search(RegPattern.URL, ptext)
    return int(flag is not None)


def containAdvertisement(ptext: str) -> (int):
    """
    Lọc các ptext mà upper letter chiếm hơn 1 nữa độ dài chuổi

    Args:
        ptext (str): review

    Returns:
        [int]: 1 nếu upper letter chiếm hơn 1 nữa độ dài chuổi, otherwise 0
    """
    upper_letters = re.findall(r'[A-Z]', ptext) # thay các upper letter thành ''
    return len(upper_letters) > 0.5 * len(ptext)


def extractEmoji(ptext: str) -> (str):
    """
    Trích xuất emoji từ comment

    Args:
        ptext (str): comment

    Returns:
        [str]: string chứa các emoji
    """
    return ' '.join(list(emojis.get(ptext)))


def normalizeComment(ptext: str, plower: bool = True) -> (str):
    """
    Chuẩn hóa text bằng cách lower nó sau đó sử dụng phương pháp NFD để biểu diễn text

    Args:
        ptext (str): comment
        plower (bool): có lower ko

    Returns:
        [str]: comment đã lower và chuẩn hóa
    """
    if isinstance(ptext, str):  # Check if ptext is a string
        ptext = ptext.lower() if plower else ptext
        return unicodedata.normalize('NFD', ptext)
    else:
        return str(ptext)


def removeSpecialLetters(ptext: str) -> (str):
    """
    Dùng xóa các kí tự đặc biệt

    Args:
        ptext (str): comment

    Returns:
        [str]: comment without special characters
    """
    return re.sub("\s+", " ", re.sub(RegPattern.UTF8_LOWER, " ", ptext)).strip() 


def removeDuplicateLetters(ptext: str) -> (str):
    """
    Hàm dùng xóa các kí tự bị dupplucate, giả sử :
      * ptext = 'okkkkkkkkkkkkkkkkkkkkkk chờiiiiiiiiii ơiiiiiiii xinhhhhhhhhhhhh quá đẹppppppppp xỉuuuuuuu'
      * Sau khi dùng hàm này thì thành:
        ptext = 'ok chời ơi xinh quá đẹp xỉu'
      
    Args:
        ptext (str): comment

    Returns:
        [str]: comment that removing duplicated letters 
    """
    return re.sub(r'(.)\1+', r'\1', ptext)


def replaceWithDictionary(ptext: str, pdictionary: Dict[str, str]) -> (str):
    """
    Hàm này dùng để thay thế các từ đơn trong ptext mà là key của pdictionary, sau đó
    thay thế từ này bằng value tương ứng với key đó.

    Args:
        ptext (str): comment
        pdictionary (Dict[str, str]): dictionary

    Returns:
        (str): comment đã dc thay thế bởi các value match với pdictionary
    """
    ptext = re.sub(r'(\s)\1+', r'\1', ptext)
    words = ptext.strip().split(' ')
    new_words = []
    
    for word in words:
        word = word.strip()
        
        if word == '': continue
        
        word = removeDuplicateLetters(word)
        word = pdictionary.get(word, word)
        new_words.append(word)
        
    return ' '.join(new_words).strip()


def removeNoiseWord(ptext: str, pdictionary: Dict[str, bool], penchantEN) -> (str):
    """
    Xóa các từ rác

    Args:
        ptext (str): comment
        pdictionary (Dict[str, bool]): từ điển tiếng việt
        penchantEN (pyenchant object): kiểm tra một từ ko phải tiếng việt thì có phải tiếng anh ko 

    Returns:
        (str): new comment without garbage words
    """
    ptext = re.sub(r'(\s)\1+', r'\1', ptext).strip()
    words = ptext.split(' ')
    new_words = []
    english_cnt = 0
    vietnam_cnt = 0
    
    for word in words:
        word = word.strip()
        no_duplicate_word = removeDuplicateLetters(word)
        
        if word == '' or no_duplicate_word == '': continue
        
        
        if pdictionary.get(no_duplicate_word, False) == True: # kiếm tra word có trong tiếng việt ko
            vietnam_cnt += 1
            new_words.append(no_duplicate_word)
        elif penchantEN.check(word) == True: # kiếm tra từ có trong tiếng anh ko
            english_cnt += 1
            new_words.append(word)
            
    if english_cnt > vietnam_cnt or vietnam_cnt == 0: # nếu một câu mà từ tiếng anh nhiều hơn tiếng việt
        return ''
    else:
        return ' '.join(new_words).strip()
    
    
def removeEmptyOrDuplicateComment(previews: udt.Dataframe) -> (udt.Dataframe):
    """
    Xóa các empty hoặc duplicate sample

    Args:
        previews (udt.Dataframe): comment

    Returns:
        (udt.Datafrane):
    """
    previews = previews[previews['normalized_comment'] != '']
    previews = previews.drop_duplicates(subset=['normalized_comment'])
    
    return previews.reset_index(drop=True)


def printAfterProcess(pdataframe: pd.DataFrame, pcolumnName: str = 'label'):
    """
    Dùng để in các giá trị về shape, số lượng các sample của từng nhóm mỗi khi ta chỉnh
    sửa dataframe

    Args:
        pdataframe (pd.DataFrame): các reviews
        pcolumnName (str): cột cần value_count
    """
    print(f"Shape: {pdataframe.shape}")
    print(pdataframe[pcolumnName].value_counts())
    