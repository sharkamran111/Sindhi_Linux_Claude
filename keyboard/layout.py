# "Sindhi" keyboard (key by key): single source of truth.
# Used by the SindhOS IBus engine (keyboard/roman/engine.py) and the keyboard guide (gen.py).
LOWER = {
 "q":"ح","w":"ڍ","e":"پ","r":"خ","t":"ڌ","y":"ر","u":"ڏ","i":"ٺ","o":"چ","p":"ڇ",
 "a":"ا","s":"د","d":"ڀ","f":"ت","g":"ٿ","h":"ٽ","j":"ث","k":"ج","l":"ڄ",
 "z":"ڙ","x":"ذ","c":"ٻ","v":"ڊ","b":"ب","n":"ڃ","m":"جھ",
}
UPPER = {
 "Q":"گھ","W":"و","E":"ض","R":"ڳ","T":"م","Y":"ي","U":"ن","I":"غ","O":"گ","P":"ڱ",
 "A":"ز","S":"ل","D":"ص","F":"ط","G":"ظ","H":"ع","J":"ف","K":"ڦ","L":"ق",
 "Z":"ء","X":"ه","C":"ش","V":"ڻ","B":"س","N":"ک","M":"ڪ",
}
MARKS = [
 ("1","َ","Zabar","زبر"),("2","ِ","Zer","زير"),("3","ُ","Pesh","پيش"),
 ("4","ّ","Shadd","شد"),("5","ْ","Jazm","جزم"),("6","آ","Alif Madda","الف مد"),
 ("7","ؤ","Wao with Hamza","واءُ همزي سان"),("8","ئ","Ye with Hamza","يءُ همزي سان"),
 ("9","ـ","Tatweel","ڪشيدو"),("0","ة","Teh Marbuta","ة"),
]
PUNCT = [
 (".","۔","Sindhi full stop","پورو دم"),(",","،","Sindhi comma","ٿورو دم"),
 ("?","؟","Question mark","سوالي نشاني"),(";","؛","Semicolon","اڌ دم"),
]
