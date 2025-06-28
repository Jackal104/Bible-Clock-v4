#!/usr/bin/env python3
"""
Generate sample data files for Bible Clock development.
"""

import json
import requests
from pathlib import Path

def generate_kjv_sample():
    """Generate a sample KJV Bible file."""
    # This is a minimal sample - in production you'd want the full Bible
    sample_bible = {
        "Genesis": {
            "1": {
                "1": "In the beginning God created the heaven and the earth.",
                "2": "And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
                "3": "And God said, Let there be light: and there was light.",
                "4": "And God saw the light, that it was good: and God divided the light from the darkness.",
                "5": "And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day."
            },
            "2": {
                "1": "Thus the heavens and the earth were finished, and all the host of them.",
                "2": "And on the seventh day God ended his work which he had made; and he rested on the seventh day from all his work which he had made.",
                "3": "And God blessed the seventh day, and sanctified it: because that in it he had rested from all his work which God created and made."
            }
        },
        "John": {
            "1": {
                "1": "In the beginning was the Word, and the Word was with God, and the Word was God.",
                "2": "The same was in the beginning with God.",
                "3": "All things were made by him; and without him was not any thing made that was made.",
                "4": "In him was life; and the life was the light of men.",
                "5": "And the light shineth in darkness; and the darkness comprehended it not."
            },
            "3": {
                "16": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
                "17": "For God sent not his Son into the world to condemn the world; but that the world through him might be saved.",
                "18": "He that believeth on him is not condemned: but he that believeth not is condemned already, because he hath not believed in the name of the only begotten Son of God."
            }
        },
        "Psalms": {
            "1": {
                "1": "Blessed is the man that walketh not in the counsel of the ungodly, nor standeth in the way of sinners, nor sitteth in the seat of the scornful.",
                "2": "But his delight is in the law of the LORD; and in his law doth he meditate day and night.",
                "3": "And he shall be like a tree planted by the rivers of water, that bringeth forth his fruit in his season; his leaf also shall not wither; and whatsoever he doeth shall prosper."
            },
            "23": {
                "1": "The LORD is my shepherd; I shall not want.",
                "2": "He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
                "3": "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
                "4": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.",
                "5": "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over.",
                "6": "Surely goodness and mercy shall follow me all the days of my life: and I will dwell in the house of the LORD for ever."
            },
            "46": {
                "1": "God is our refuge and strength, a very present help in trouble.",
                "2": "Therefore will not we fear, though the earth be removed, and though the mountains be carried into the midst of the sea;",
                "3": "Though the waters thereof roar and be troubled, though the mountains shake with the swelling thereof. Selah."
            }
        },
        "Proverbs": {
            "3": {
                "1": "My son, forget not my law; but let thine heart keep my commandments:",
                "2": "For length of days, and long life, and peace, shall they add to thee.",
                "3": "Let not mercy and truth forsake thee: bind them about thy neck; write them upon the table of thine heart:",
                "4": "So shalt thou find favour and good understanding in the sight of God and man.",
                "5": "Trust in the LORD with all thine heart; and lean not unto thine own understanding.",
                "6": "In all thy ways acknowledge him, and he shall direct thy paths."
            }
        },
        "Romans": {
            "8": {
                "28": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
                "29": "For whom he did foreknow, he also did predestinate to be conformed to the image of his Son, that he might be the firstborn among many brethren.",
                "30": "Moreover whom he did predestinate, them he also called: and whom he called, them he also justified: and whom he justified, them he also glorified."
            }
        },
        "Philippians": {
            "4": {
                "13": "I can do all things through Christ which strengtheneth me.",
                "14": "Notwithstanding ye have well done, that ye did communicate with my affliction.",
                "15": "Now ye Philippians know also, that in the beginning of the gospel, when I departed from Macedonia, no church communicated with me as concerning giving and receiving, but ye only."
            }
        },
        "Matthew": {
            "11": {
                "28": "Come unto me, all ye that labour and are heavy laden, and I will give you rest.",
                "29": "Take my yoke upon you, and learn of me; for I am meek and lowly in heart: and ye shall find rest unto your souls.",
                "30": "For my yoke is easy, and my burden is light."
            }
        },
        "Isaiah": {
            "40": {
                "31": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."
            }
        },
        "Jeremiah": {
            "29": {
                "11": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end."
            }
        },
        "1 John": {
            "4": {
                "19": "We love him, because he first loved us.",
                "20": "If a man say, I love God, and hateth his brother, he is a liar: for he that loveth not his brother whom he hath seen, how can he love God whom he hath not seen?",
                "21": "And this commandment have we from him, That he who loveth God love his brother also."
            }
        }
    }
    
    output_path = Path('data/translations/bible_kjv.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sample_bible, f, indent=2)
    
    print(f"Enhanced KJV Bible sample saved to {output_path}")

def generate_extended_fallback_verses():
    """Generate an extended set of fallback verses."""
    extended_verses = [
        {
            "reference": "John 3:16",
            "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            "book": "John",
            "chapter": 3,
            "verse": 16
        },
        {
            "reference": "Psalm 23:1",
            "text": "The LORD is my shepherd; I shall not want.",
            "book": "Psalms",
            "chapter": 23,
            "verse": 1
        },
        {
            "reference": "Romans 8:28",
            "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
            "book": "Romans",
            "chapter": 8,
            "verse": 28
        },
        {
            "reference": "Philippians 4:13",
            "text": "I can do all things through Christ which strengtheneth me.",
            "book": "Philippians",
            "chapter": 4,
            "verse": 13
        },
        {
            "reference": "Proverbs 3:5-6",
            "text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths.",
            "book": "Proverbs",
            "chapter": 3,
            "verse": 5
        },
        {
            "reference": "Isaiah 40:31",
            "text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint.",
            "book": "Isaiah",
            "chapter": 40,
            "verse": 31
        },
        {
            "reference": "Matthew 11:28",
            "text": "Come unto me, all ye that labour and are heavy laden, and I will give you rest.",
            "book": "Matthew",
            "chapter": 11,
            "verse": 28
        },
        {
            "reference": "Jeremiah 29:11",
            "text": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end.",
            "book": "Jeremiah",
            "chapter": 29,
            "verse": 11
        },
        {
            "reference": "1 John 4:19",
            "text": "We love him, because he first loved us.",
            "book": "1 John",
            "chapter": 4,
            "verse": 19
        },
        {
            "reference": "Psalm 46:1",
            "text": "God is our refuge and strength, a very present help in trouble.",
            "book": "Psalms",
            "chapter": 46,
            "verse": 1
        },
        {
            "reference": "John 1:1",
            "text": "In the beginning was the Word, and the Word was with God, and the Word was God.",
            "book": "John",
            "chapter": 1,
            "verse": 1
        },
        {
            "reference": "Genesis 1:1",
            "text": "In the beginning God created the heaven and the earth.",
            "book": "Genesis",
            "chapter": 1,
            "verse": 1
        },
        {
            "reference": "Psalm 1:1",
            "text": "Blessed is the man that walketh not in the counsel of the ungodly, nor standeth in the way of sinners, nor sitteth in the seat of the scornful.",
            "book": "Psalms",
            "chapter": 1,
            "verse": 1
        },
        {
            "reference": "Matthew 6:9",
            "text": "After this manner therefore pray ye: Our Father which art in heaven, Hallowed be thy name.",
            "book": "Matthew",
            "chapter": 6,
            "verse": 9
        },
        {
            "reference": "1 Corinthians 13:4",
            "text": "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up,",
            "book": "1 Corinthians",
            "chapter": 13,
            "verse": 4
        }
    ]
    
    output_path = Path('data/fallback_verses.json')
    with open(output_path, 'w') as f:
        json.dump(extended_verses, f, indent=2)
    
    print(f"Extended fallback verses saved to {output_path}")

def check_api_connectivity():
    """Check if Bible API is accessible and get sample data."""
    try:
        response = requests.get("https://bible-api.com/john%203:16", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Bible API is accessible")
            print(f"Sample response: {data.get('reference', 'N/A')}")
            return True
        else:
            print(f"❌ Bible API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach Bible API: {e}")
        return False

def main():
    """Generate all sample data files."""
    print("Bible Clock Sample Data Generator")
    print("=" * 40)
    
    # Check API connectivity
    api_available = check_api_connectivity()
    print()
    
    # Generate sample files
    print("Generating sample data files...")
    generate_kjv_sample()
    generate_extended_fallback_verses()
    
    print()
    print("Sample data generation complete!")
    print()
    print("Files created:")
    print("- data/translations/bible_kjv.json (enhanced sample)")
    print("- data/fallback_verses.json (extended set)")
    print()
    
    if api_available:
        print("✅ Online Bible API is available for additional verses")
    else:
        print("⚠️  Online Bible API not available - will use local data only")

if __name__ == '__main__':
    main()