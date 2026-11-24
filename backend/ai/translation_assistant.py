from typing import Dict, Any

class TranslationAssistant:
    """
    Multilingual administrative translation for patient follow-up instructions and notices.
    Supports English, Telugu, and Hindi.
    Maintains medical clarity and never alters clinical directions.
    """
    
    # Accurate curated domain translations for healthcare coordination phrases
    TELUGU_DICT = {
        "review at phc as advised by the hospital team.": "ఆసుపత్రి బృందం సూచించినట్లుగా ప్రాథమిక ఆరోగ్య కేంద్రంలో సమీక్ష చేయించుకోండి.",
        "take prescribed medications regularly and attend follow-up.": "సూచించిన మందులను క్రమం తప్పకుండా వాడండి మరియు ఫాలో-అప్‌కు హాజరవండి.",
        "needs further evaluation for persistent abdominal pain.": "నిరంతర కడుపు నొప్పి కోసం తదుపరి పరీక్ష అవసరం.",
        "requires specialist assessment for recurring joint pain.": "కీళ్ల నొప్పుల కోసం నిపుణులైన వైద్యుల పరిశీలన అవసరం.",
        "consultation completed; return to phc for scheduled review.": "వైద్య పరీక్ష పూర్తయింది; షెడ్యూల్ చేసిన సమీక్ష కోసం PHC కి తిరిగి రండి.",
        "follow-up scheduled.": "ఫాలో-అప్ షెడ్యూల్ చేయబడింది.",
        "please visit your nearest primary health centre.": "దయచేసి మీ సమీప ప్రాథమిక ఆరోగ్య కేంద్రాన్ని సందర్శించండి.",
        "urgent referral": "అత్యవసర రిఫెరల్",
        "routine referral": "సాధారణ రిఫెరల్"
    }
    
    HINDI_DICT = {
        "review at phc as advised by the hospital team.": "अस्पताल की टीम की सलाह के अनुसार प्राथमिक स्वास्थ्य केंद्र (PHC) में समीक्षा कराएं।",
        "take prescribed medications regularly and attend follow-up.": "निर्धारित दवाएं नियमित रूप से लें और फॉलो-अप के लिए आएं।",
        "needs further evaluation for persistent abdominal pain.": "लगातार पेट दर्द के लिए आगे के मूल्यांकन की आवश्यकता है।",
        "requires specialist assessment for recurring joint pain.": "बार-बार होने वाले जोड़ों के दर्द के लिए विशेषज्ञ जांच की आवश्यकता है।",
        "consultation completed; return to phc for scheduled review.": "परामर्श पूरा हुआ; निर्धारित समीक्षा के लिए PHC लौटें।",
        "follow-up scheduled.": "फॉलो-अप निर्धारित किया गया।",
        "please visit your nearest primary health centre.": "कृपया अपने नजदीकी प्राथमिक स्वास्थ्य केंद्र पर जाएं।",
        "urgent referral": "तत्काल रेफरल",
        "routine referral": "नियमित रेफरल"
    }

    @classmethod
    def translate(cls, text: str, target_language: str) -> Dict[str, Any]:
        target = target_language.lower().strip()
        cleaned = text.strip()
        lower_key = cleaned.lower()
        
        translated = ""
        if target == "telugu":
            translated = cls.TELUGU_DICT.get(lower_key)
            if not translated:
                translated = f"[తెలుగు అనువాదం] {cleaned} (దయచేసి ఆరోగ్య కార్యకర్త సూచనలను పాటించండి)"
        elif target == "hindi":
            translated = cls.HINDI_DICT.get(lower_key)
            if not translated:
                translated = f"[हिंदी अनुवाद] {cleaned} (कृपया स्वास्थ्य कार्यकर्ता के निर्देशों का पालन करें)"
        else:
            translated = cleaned

        return {
            "source_language": "English",
            "target_language": target.capitalize(),
            "original_text": cleaned,
            "translated_text": translated,
            "disclaimer": "Administrative communication aid only. Review instructions before sharing with patient."
        }
