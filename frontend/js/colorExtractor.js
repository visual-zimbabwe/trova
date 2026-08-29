// Trova Dominant Color Palette Extractor

const ColorExtractor = {
  extractDominantColor(imageUrl) {
    return new Promise((resolve) => {
      if (!imageUrl) {
        resolve(null);
        return;
      }

      const img = new Image();
      img.crossOrigin = 'Anonymous';
      img.src = imageUrl;

      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          canvas.width = 64;
          canvas.height = 64;
          ctx.drawImage(img, 0, 0, 64, 64);

          const imgData = ctx.getImageData(0, 0, 64, 64).data;
          let rTotal = 0, gTotal = 0, bTotal = 0, count = 0;

          for (let i = 0; i < imgData.length; i += 16) {
            const r = imgData[i];
            const g = imgData[i + 1];
            const b = imgData[i + 2];
            // Skip overly dark/black and near-white pixels
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
            if (brightness > 30 && brightness < 220) {
              rTotal += r;
              gTotal += g;
              bTotal += b;
              count++;
            }
          }

          if (count > 0) {
            const rAvg = Math.round(rTotal / count);
            const gAvg = Math.round(gTotal / count);
            const bAvg = Math.round(bTotal / count);
            resolve(`rgb(${rAvg}, ${gAvg}, ${bAvg})`);
          } else {
            resolve(null);
          }
        } catch (e) {
          resolve(null);
        }
      };

      img.onerror = () => resolve(null);
    });
  },

  applyAmbientAura(color) {
    if (color) {
      document.documentElement.style.setProperty('--om-aura-color', color);
    }
  }
};
