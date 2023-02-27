
library(ggplot2)
library(ggpubr)
library(knitr)
library(gridExtra)
library(magick)


contours_pic = image_read("contours.jpg")
contours_pic=image_scale(contours_pic,1500)

picture <- ggplot() + 
  background_image(contours_pic) +
  # This ensures that the image leaves some space at the edges
  theme(aspect.ratio = 2250/3000)


area_data = read.csv("area_mm.csv", header=T)
colnames(area_data) = c("pixels", "mm2", "length", "width")

histogram = ggplot(area_data, aes(mm2))+geom_histogram()

stats=summary(area_data$mm2)
names(stats)
stats_df=data.frame(as.list(stats))
colnames(stats_df)=c("Min.",    "1st Qu.", "Median",  "Mean" ,   "3rd Qu." ,"Max." )
stats_df$number_objects = nrow(area_data)

stats_df=t(stats_df)
colnames(stats_df)="Square Millimeters"
stats_df=round(stats_df,digits=3)

table=tableGrob(stats_df)

layout = rbind(c(1,1,1),
               c(1,1,1),
               c(2,2,3))

#layout = rbind(c(1,1,3),
#               c(1,1,3),
#               c(2,2,3))

jpeg(filename = "stats.jpg", width=1000,height=775)
grid.arrange(picture, histogram, table,layout_matrix=layout)
dev.off()