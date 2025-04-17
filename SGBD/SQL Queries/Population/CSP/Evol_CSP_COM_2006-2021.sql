-- Évolution des CSP dans une commune de 2006 à 2021
-- Exemple de Suresnes

WITH all_years AS (
  -- 2021
  SELECT '2021' as annee,
         SUM(C21_POP15P_CS1) as "Agriculteurs exploitants",
         SUM(C21_POP15P_CS2) as "Artisans, Commerçants, Chefs d'entreprise",
         SUM(C21_POP15P_CS3) as "Cadres, Prof. intel. sup.",
         SUM(C21_POP15P_CS4) as "Prof. intermédiaires",
         SUM(C21_POP15P_CS5) as "Employés",
         SUM(C21_POP15P_CS6) as "Ouvriers",
         SUM(C21_POP15P_CS7) as "Retraités",
         SUM(C21_POP15P_CS8) as "Autres sans activité prof."
  FROM POP_IRIS_2021
  WHERE COM = '92073'

  UNION ALL
  
  -- 2016
  SELECT '2016' as annee,
         SUM(C16_POP15P_CS1) as "Agriculteurs exploitants",
         SUM(C16_POP15P_CS2) as "Artisans, Commerçants, Chefs d'entreprise",
         SUM(C16_POP15P_CS3) as "Cadres, Prof. intel. sup.",
         SUM(C16_POP15P_CS4) as "Prof. intermédiaires",
         SUM(C16_POP15P_CS5) as "Employés",
         SUM(C16_POP15P_CS6) as "Ouvriers",
         SUM(C16_POP15P_CS7) as "Retraités",
         SUM(C16_POP15P_CS8) as "Autres sans activité prof."
  FROM POP_IRIS_2016
  WHERE COM = '92073'

  UNION ALL
  
  -- 2011
  SELECT '2011' as annee,
         SUM(C11_POP15P_CS1) as "Agriculteurs exploitants",
         SUM(C11_POP15P_CS2) as "Artisans, Commerçants, Chefs d'entreprise",
         SUM(C11_POP15P_CS3) as "Cadres, Prof. intel. sup.",
         SUM(C11_POP15P_CS4) as "Prof. intermédiaires",
         SUM(C11_POP15P_CS5) as "Employés",
         SUM(C11_POP15P_CS6) as "Ouvriers",
         SUM(C11_POP15P_CS7) as "Retraités",
         SUM(C11_POP15P_CS8) as "Autres sans activité prof."
  FROM POP_IRIS_2011
  WHERE COM = '92073'

  UNION ALL
  
  -- 2006
  SELECT '2006' as annee,
         SUM(C06_POP15P_CS1) as "Agriculteurs exploitants",
         SUM(C06_POP15P_CS2) as "Artisans, Commerçants, Chefs d'entreprise",
         SUM(C06_POP15P_CS3) as "Cadres, Prof. intel. sup.",
         SUM(C06_POP15P_CS4) as "Prof. intermédiaires",
         SUM(C06_POP15P_CS5) as "Employés",
         SUM(C06_POP15P_CS6) as "Ouvriers",
         SUM(C06_POP15P_CS7) as "Retraités",
         SUM(C06_POP15P_CS8) as "Autres sans activité prof."
  FROM POP_IRIS_2006
  WHERE COM = '92073'
)

SELECT *
FROM all_years
ORDER BY annee;
