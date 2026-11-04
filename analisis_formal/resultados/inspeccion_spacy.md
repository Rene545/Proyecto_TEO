# Inspección de los falsos positivos de spaCy + regla

Generado por `python -m analisis_formal.inspeccionar_spacy --guardar` (spaCy 3.8.18, modelo es_core_news_sm 3.8.0).

| Oración agramatical | Clasificación | Evidencia |
| --- | --- | --- |
| los gato duermen | rasgo_vacio | "gato": Gender real=Masc, spaCy=(vacío); "gato": Number real=Sing, spaCy=(vacío) |
| el gato duermen | rasgo_vacio | "gato": Gender real=Masc, spaCy=(vacío); "gato": Number real=Sing, spaCy=(vacío) |
| el gato ve los ratón | rasgo_asimilado | "ratón": Number real=Sing, spaCy=Plur |
| el gato negra duerme | rasgo_asimilado | "negra": Gender real=Fem, spaCy=Masc |
| el gato que duermen ve el ratón | regla_relativa | "que" (obj de "duermen") no tiene número; la discordancia gato[Sing] ~ duermen[Plur] pasa por la relación acl, que la regla no revisa |
| los gatos que duerme ven los ratones | regla_relativa | "que" (nsubj de "duerme") no tiene número; la discordancia gatos[Plur] ~ duerme[Sing] pasa por la relación acl, que la regla no revisa |
| la niña que compran un libro duerme | regla_relativa | "que" (nsubj de "compran") no tiene número; la discordancia niña[Sing] ~ compran[Plur] pasa por la relación acl, que la regla no revisa |

Total: 7 falsos positivos. rasgo_asimilado: 2, rasgo_vacio: 2, regla_relativa: 3.

## Detalle por oración

### los gato duermen

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| los | DET | det | gato | Definite=Def|Gender=Masc|Number=Plur|PronType=Art |
| gato | NOUN | nsubj | duermen | (vacío) |
| duermen | VERB | ROOT | duermen | Mood=Ind|Number=Plur|Person=3|Tense=Imp|VerbForm=Fin |

### el gato duermen

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| el | DET | det | gato | Definite=Def|Gender=Masc|Number=Sing|PronType=Art |
| gato | NOUN | nsubj | duermen | (vacío) |
| duermen | VERB | ROOT | duermen | Mood=Ind|Number=Plur|Person=3|Tense=Imp|VerbForm=Fin |

### el gato ve los ratón

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| el | DET | det | gato | Definite=Def|Gender=Masc|Number=Sing|PronType=Art |
| gato | NOUN | nsubj | ve | Gender=Masc|Number=Sing |
| ve | VERB | ROOT | ve | Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin |
| los | DET | det | ratón | Definite=Def|Gender=Masc|Number=Plur|PronType=Art |
| ratón | NOUN | obj | ve | Gender=Masc|Number=Plur |

### el gato negra duerme

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| el | DET | det | gato | Definite=Def|Gender=Masc|Number=Sing|PronType=Art |
| gato | NOUN | nsubj | duerme | Gender=Masc|Number=Sing |
| negra | ADJ | amod | gato | Gender=Masc|Number=Sing |
| duerme | VERB | ROOT | duerme | Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin |

### el gato que duermen ve el ratón

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| el | DET | det | gato | Definite=Def|Gender=Masc|Number=Sing|PronType=Art |
| gato | NOUN | nsubj | ve | Gender=Masc|Number=Sing |
| que | PRON | obj | duermen | PronType=Int,Rel |
| duermen | VERB | acl | gato | Mood=Sub|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin |
| ve | VERB | ROOT | ve | Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin |
| el | DET | det | ratón | Definite=Def|Gender=Masc|Number=Sing|PronType=Art |
| ratón | NOUN | obj | ve | Gender=Masc|Number=Sing |

### los gatos que duerme ven los ratones

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| los | DET | det | gatos | Definite=Def|Gender=Masc|Number=Plur|PronType=Art |
| gatos | NOUN | nsubj | ven | Gender=Masc|Number=Plur |
| que | PRON | nsubj | duerme | PronType=Int,Rel |
| duerme | VERB | acl | gatos | Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin |
| ven | VERB | ROOT | ven | Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin |
| los | DET | det | ratones | Definite=Def|Gender=Masc|Number=Plur|PronType=Art |
| ratones | NOUN | obj | ven | Gender=Masc|Number=Plur |

### la niña que compran un libro duerme

| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |
| --- | --- | --- | --- | --- |
| la | DET | det | niña | Definite=Def|Gender=Fem|Number=Sing|PronType=Art |
| niña | NOUN | nsubj | duerme | Gender=Fem|Number=Sing |
| que | PRON | nsubj | compran | PronType=Int,Rel |
| compran | VERB | acl | niña | Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin |
| un | DET | det | libro | Definite=Ind|Gender=Masc|Number=Sing|PronType=Art |
| libro | NOUN | obj | compran | Gender=Masc|Number=Sing |
| duerme | VERB | ROOT | duerme | Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin |
