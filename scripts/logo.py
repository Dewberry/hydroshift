import os
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from PIL import Image


n = 100
c1 = "#4287f5"
c1_accent = mcolors.to_hex([c * 0.8 for c in mcolors.to_rgb(c1)])
c2 = "#f5a742"
c2_accent = mcolors.to_hex([c * 0.8 for c in mcolors.to_rgb(c2)])
d1 = norm(1.5)
d2 = norm(-1.5)
s1 = d1.rvs(n)
s2 = d2.rvs(n)
fcs = [c1] * n + [c2] * n
ecs = [c1_accent] * n + [c2_accent] * n
combo = np.append(s1, s2)
pdf_range = np.linspace(d1.mean() + (3 * d1.std()), d2.mean() - (3 * d2.std()), 1000)
pdf1 = d1.pdf(pdf_range)
pdf2 = d2.pdf(pdf_range)

fig, axs = plt.subplots(ncols=2, gridspec_kw={"width_ratios": [3, 1], "wspace": 0.01}, figsize=(4, 2))
axs[0].scatter(range(len(combo)), combo, ec=ecs, fc=fcs, lw=0.35, s=2.2)
axs[0].axvline(n + 0.5, ls="dashed", c="k", alpha=0.3, lw=0.7)
axs[1].fill_betweenx(pdf_range, 0, pdf1, fc=c1, ec=c1_accent)
axs[1].fill_betweenx(pdf_range, 0, pdf2, fc=c2, ec=c2_accent)
for ax in axs:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
fig.tight_layout()
fig.savefig("hydroshift/images/logo_base.png", transparent=True, dpi=600, bbox_inches="tight", pad_inches=0)


fig, ax = plt.subplots(figsize=(1, 1))
ax.fill_between(pdf_range, 0, pdf1, fc=c1, ec=c1_accent)
ax.fill_between(pdf_range, 0, pdf2, fc=c2, ec=c2_accent)
ax.set_xticks([])
ax.set_yticks([])
ax.set_frame_on(False)
fig.tight_layout()
fig.savefig("hydroshift/images/tmp.png", transparent=True, dpi=300, bbox_inches="tight", pad_inches=0)
png_image = Image.open("hydroshift/images/tmp.png")
png_image.save("hydroshift/images/favicon.ico", format='ICO', sizes=[(32, 32), (64, 64)])
os.remove("hydroshift/images/tmp.png")
