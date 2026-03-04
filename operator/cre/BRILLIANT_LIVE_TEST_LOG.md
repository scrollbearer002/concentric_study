# Brilliant Live Test Log

## Environment
- Repo: `concentric_study`
- Browser: Safari
- Target: `https://www.brilliant.org/`
- Date: 2026-03-03

## Action Log
1. Opened Brilliant home page in Safari.
2. Read DOM surface and confirmed anonymous state (`Sign in`, `Get started`).
3. Navigated to /login and located OAuth buttons in live HTML.
4. Triggered the Google OAuth button.
5. Clicked Google OAuth button.
6. OAuth returned directly to authenticated Brilliant home page.
7. No visible Resume/Continue target found on home surface; selected the top visible Start tile.
8. Triggered the first visible Start action on the authenticated home page.
9. Entered course lesson surface: Filtering Images.
10. Advanced via Continue into the lesson body.
11. Inspected interactive shadow DOM and identified a range input controlling pixel value (initially 77).
12. Set the range input to 0 (black).
13. Verified that Check unlocked after setting the pixel value to 0.
14. Submitted the first exercise.
15. First exercise passed: Correct (+15 XP).
16. Advanced to the next lesson page.
17. Inspected page 3 and found two separate range inputs; first already at 0, second at 218.
18. Set the second range input to 255 (white).
19. Submitted page 3 and passed: Correct (+15 XP).
20. Advanced to the next lesson page.
21. Page 4 contained a token-fill code puzzle with explicit slots for condition and assignment.
22. DOM click simulation was insufficient; switched to native Quartz drag using live Safari window bounds plus shadow-DOM geometry.
23. Filled the code puzzle as `if pixel < 128` then `pixel = 0`, which enabled Check.
24. Submitted the page 4 solution.
25. Page 4 passed: Correct (+15 XP).
26. Advanced to the next lesson page.
27. Page 5 exposed two stacked code puzzles; the first was already solved from page 4.
28. Enumerated the second shadow-DOM interactive and identified the remaining blanks as `pixel = 255` under the `else` branch.
29. Used native Quartz drag again; first pass landed `255`, second pass recalculated live geometry and landed `pixel`.
30. Submitted the page 5 solution.
31. Page 5 passed: Correct (+15 XP).
32. Advanced to the next lesson page.
33. Page 6 was a narrative transition page confirming the image-filter milestone.
34. Advanced past the transition page.
35. Entered the first post-intro practice interactive.
36. Shadow-DOM inspection showed the visible required branch value already filled and the page exposing Continue, so advanced rather than forcing redundant interaction.
37. Advanced into the first post-intro practice update prompt: replace the lighter-pixel value from white to gray.
38. Verified the live state expects a change from `255` to `180` in the `else` branch.
39. Native Quartz drag and native tap both succeeded on earlier fill puzzles but did not mutate the occupied post-intro replacement slot.
40. Recorded the current blocker as an edit-style slot replacement interaction on the practice problem.
41. Saved current screenshot to `operator/cre/brilliant_live_state_4.png`.
