# SeePD BTK Hangasszisztens (FiveM / SeeRPG)

Egy modern, hangalapú Windows segédalkalmazás SeeMTA / SeeRPG rendvédelmi (PD) szerepjátékosok számára.
A gombnyomásra (F9) rögzített beszéd alapján az ingyenes **Google Gemini API** segítségével valós időben felismeri az elkövetett szabálysértéseket és a hatályos **SeePD BTK** adatbázis alapján azonnal kalkulálja az összevont büntetési tételeket.

## Főbb Funkciók

- **Gyorsbillentyű (Hotkey):** F9 megnyomásával indul és áll le a rögzítés (Toggle / Push-to-Talk támogatás).
- **Élő SeePD BTK Szinkronizáció:** Automatikusan letölti és gyorsítótárazza a legfrissebb büntetőpontokat (`https://btkapi.seepd.hu/btk`).
- **Valós idejű In-Game HUD:** Letisztult, keretmentes, lebegő és átlátszó panel, amely a játék felett jeleníti meg a büntetés összegét, börtönidőt és jogosítvány státuszt.
- **Azonnali Vágólap (Ctrl+V):** A felismert BTK kódokat azonnal a vágólapra másolja a gyors FiveM beillesztéshez.
- **Belső Hangbemondás (TTS):** Diszkrét hangos bemondás közvetlenül a fülhallgatóba.
- **Dinamikus AI Modellválasztó:** Támogatja a legújabb `gemini-3.1-flash-lite`, `gemini-2.0-flash-lite` és `gemini-2.5-flash` modelleket.
- **100% Vektoros SVG Ikonok:** Emoji-mentes, modern felület.

## Használat

1. Indítsd el a `SeePDBTKAssistant.exe` alkalmazást.
2. A Windows tálcán a rendőrségi jelvényre jobb gombbal kattintva nyisd meg a **Beállítások** ablakot.
3. Másold be az ingyenes Google AI Studio API kulcsodat ([aistudio.google.com](https://aistudio.google.com/app/apikey)).
4. A játékban nyomd meg az **F9** gombot, mondd be a szabálysértéseket (pl. *"Gyorshajtás és átment a piroson"*), majd nyomd meg újra az **F9**-et.

## Licenc

Ez a projekt nyílt forráskódú az [MIT Licenc](LICENSE) feltételei szerint.
