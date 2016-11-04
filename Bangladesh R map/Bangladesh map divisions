library(foreign)
require(graphics)
library(maptools)
library(fields)


#Load the appropriate rds file from the website http://www.gadm.org/version2
# There are 4 levels of granularity
G0<-readRDS("/Users/ruth/Desktop/Nutrition/Bangladesh R map/BGD_adm0.rds")
G1<-readRDS("/Users/ruth/Desktop/Nutrition/Bangladesh R map/BGD_adm1.rds")
G2<-readRDS("/Users/ruth/Desktop/Nutrition/Bangladesh R map/BGD_adm2.rds")
G3<-readRDS("/Users/ruth/Desktop/Nutrition/Bangladesh R map/BGD_adm3.rds")



#Names of the districts at different levels
G1$NAME_1<-as.factor(G1$NAME_1)
G2$NAME_2<-as.factor(G2$NAME_2)
G3$NAME_3<-as.factor(G3$NAME_3)

# This is making a table of disctricts and their values (random uniform at the moment) to be coloured. Could easily read this in from excel
values1<-as.data.frame(G1$NAME_1)
#values1$density<-runif(length(values1[,1]),0,1)
numStuntAvert<-c(77104, 285304, 447721, 87600, 135460, 56975, 50571) 
values1$density<-numStuntAvert


# level 1 region plot------

####PNG outputs. I actually split it up as a multipanel plot so that the legend colourbar could go below.

b <- 0.5

zc <- as.matrix(seq(min(values1$density), max(values1$density), length.out=100))
mycolor1 <- two.colors(n=100, start=rgb(1,1,b,alpha=0.75), end=rgb(0,1,b,alpha=0.75), middle=rgb(0.5,1,b,alpha=0.75))


png(file="/Users/ruth/Desktop/Nutrition/Bangladesh R map/BNG_level1.png",width=5, height=6, units="in", res=300)
layout(matrix(c(1,2), 2, 1, byrow = TRUE), heights=c(8,1), widths=c(4) )
layout.show(2) 
par(mar=c(0,0,0,0), oma=c(0,0,2,0))

#plot(G1,col=rgb(1,1-values1$density,0,alpha=0.75), add=F, lwd=1, border=F)
plot(G1,col=rgb(1-(values1$density-min(values1$density))/(max(values1$density)-min(values1$density)),1,b,alpha=0.75), add=F, lwd=1, border=F)

invisible(text(getSpPPolygonsLabptSlots(G1), labels=as.character(G1$NAME_1), cex=0.75, col="black", font=1))
#mtext(side=3, line=0, "optimized geospatial spending", cex=1.5)
par(mar=c(1.5,1,1,2))
image(zc, col=mycolor1, axes=F, xlab="", ylab="" )
mtext("stunting cases averted")
#tidylabels <- round(seq(min(values1$density),max(values1$density),length.out=5))
tidylabels <- c(50000, 150000, 250000, 350000, 450000)
axis(1, at=seq(0,1, length.out=5),  labels=tidylabels, las=1,  tcl=-.15, padj=-1, cex=0.5)
dev.off()




