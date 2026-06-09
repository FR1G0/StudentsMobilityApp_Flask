import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = 'Students Mobility App';

  links : link[] = [
    {
      text: 'Home',
      href: '/home'
    },
    {
      text: 'Applications',
      href: '/application-list'
    },
  ];
}

interface link {
  text: string;
  href: string;
}
