# Assets – דיאגרמות הקורס

| קובץ | שיעור | תוכן |
|------|--------|------|
| [01-שקפים.html](01-שקפים.html) | 01 | שקף ML vs LLM + דיאגרמת FC + הפניה לדמו. לפתוח בדפדפן, F11 |
| function-calling-flow.svg | 01 | זרימת Function Calling: Query → Tool Call → Result → Response |
| mcp-client-tools-flow.png | 07 | Client מפעיל Tools מול אשכול שרתים/כלים (MCP) |

## איך לעדכן

אם התמונות עדיין לא כאן, העתיקו מתיקיית Cursor / מהצ'אט בשמות למעלה.

השיעורים 01 ו-07 מקשרים לשמות הקבצים האלה.

### ASCII fallback – Function Calling

```text
User --Query--> Bot (tools defined, not run)
Bot --Query+Tools--> Model (which function?)
Model --Tool Call--> Bot (run function with args)
Bot --Query+Call+Result--> Model
Model --Completion--> Bot
Bot --Response--> User
```

### ASCII fallback – MCP

```text
[ MCP Servers / Tools cluster ]  >>>  Client: "מפעיל את ה-Tool דרך ה-Client"
```
